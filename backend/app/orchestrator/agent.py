import os
from typing import AsyncIterable
import asyncio
import logging
import json
from collections import deque

from app.services.key_manager_gemini import key_manager
from app.orchestrator.retriever import search_knowledge
from app.utils.prompts import (
    ORCHESTRATOR_INTENT_PROMPT,
    RAG_ANSWER_PROMPT,
    QUIZ_GENERATION_PROMPT,
    IMAGE_GENERATION_PROMPT,
    GENERAL_CHAT_PROMPT,
    QUERY_REFINER_PROMPT,
)

logger = logging.getLogger(__name__)

if not key_manager:
    raise RuntimeError("Gemini API keys are not configured on the server.")

# Timeout configuration
RETRIEVAL_TIMEOUT = 30  # Maximum time for knowledge retrieval (seconds)
GENERATION_TIMEOUT = 120  # Maximum time for text generation (seconds)
IMAGE_GENERATION_TIMEOUT = 60  # Maximum time for image generation (seconds)


class HistoryAIAgent:
    def __init__(self) -> None:
        self.key_manager = key_manager
        self.memory_window = deque(maxlen=6) 

    def _infer_intent_fast(self, user_input: str) -> str | None:
        s = user_input.lower()
        quiz_keywords = [
            "quiz",
            "trắc nghiệm",
            "câu hỏi",
            "đề",
            "bài tập",
            "kiểm tra",
            "luyện tập",
            "đáp án",
        ]
        if any(k in s for k in quiz_keywords):
            return "QUIZ"
        return None

    async def orchestrator(self, user_input: str) -> dict:
        prompt = ORCHESTRATOR_INTENT_PROMPT.format(user_input=user_input)
        response = self.key_manager.generate_content(prompt)
        try:
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"❌ Orchestrator error: {e}")
            return {"intent": "LEARN", "need_image": False}

    async def _generate_image_task(self, user_input: str, context_text: str) -> tuple[str, str] | None:
        try:
            prompt_resp = await asyncio.to_thread(
                self.key_manager.generate_content,
                IMAGE_GENERATION_PROMPT.format(user_input=user_input, context=context_text[:1500]),
            )
            image_prompt = (prompt_resp.text or "").strip()
            
            #gen image
            image_result = await asyncio.to_thread(
                self.key_manager.generate_image, image_prompt
            )
            return image_result
        except Exception as e:
            logger.error(f"❌ Async image task error: {e}")
            return None

    async def rag_agent_stream(self, user_input: str) -> AsyncIterable[str]:
        try:
            clean_query  = await self._refine_user_query(user_input)
            chat_history_str = self._get_history_string()

            knowledges = await asyncio.to_thread(search_knowledge, clean_query, use_hybrid=True)
            context = "\n\n".join([k['content_text'] for k in knowledges])
            
            prompt = RAG_ANSWER_PROMPT.format(
                context=context,
                chat_history=chat_history_str,
                user_input=user_input
            )
            
            full_response = ""
            for chunk_text in self.key_manager.stream_content(prompt, use_stream_config=True):
                if chunk_text:
                    full_response += chunk_text
                    yield json.dumps({"type": "text", "content": chunk_text}, ensure_ascii=False) + "\n"
            
            self.memory_window.append({"role": "Học sinh", "content": user_input})
            self.memory_window.append({"role": "Giáo viên", "content": full_response})

        except Exception as e:
            logger.error(f"RAG agent error: {e}")
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"

    async def quiz_agent_stream(self, user_input: str) -> AsyncIterable[str]:
        try:
            yield json.dumps({
                "type": "status",
                "message": "Searching for documents to generate quiz..."
            }, ensure_ascii=False) + "\n"
            
            # Convert blocking search to async with timeout
            try:
                knowledges = await asyncio.wait_for(
                    asyncio.to_thread(search_knowledge, user_input, limit=3, use_hybrid=True),
                    timeout=RETRIEVAL_TIMEOUT
                )
            except asyncio.TimeoutError:
                yield json.dumps({
                    "type": "error",
                    "code": "RETRIEVAL_TIMEOUT",
                    "message": "Searching for documents took too long. Please try again."
                }, ensure_ascii=False) + "\n"
                return
            
            if not knowledges:
                yield json.dumps({
                    "type": "error",
                    "code": "NO_KNOWLEDGE_FOUND",
                    "message": "No documents found to generate quiz."
                }, ensure_ascii=False) + "\n"
                return

            context_parts = []
            for k in knowledges:
                page_info = f"[Trang {k.get('page_id', '?')} - {k.get('topic', '')}]"
                context_parts.append(f"{page_info}\n{k['content_text']}")
            
            context = "\n\n---\n\n".join(context_parts)
            
            # Status: Generating quiz
            yield json.dumps({
                "type": "status",
                "message": "Generating quiz..."
            }, ensure_ascii=False) + "\n"

            prompt = QUIZ_GENERATION_PROMPT.format(
                context=context,
                user_input=user_input,
            )
            
            for text in self.key_manager.stream_content(prompt, use_stream_config=True):
                if text:
                    data = json.dumps(
                        {"type": "text", "content": text},
                        ensure_ascii=False,
                    )
                    yield f"{data}\n"
                    
        except asyncio.TimeoutError:
            yield json.dumps({
                "type": "error",
                "code": "TIMEOUT",
                "message": "Request timed out. Please try again."
            }, ensure_ascii=False) + "\n"
        except Exception as e:
            logger.error(f"Quiz agent error: {e}", exc_info=True)
            yield json.dumps({
                "type": "error",
                "code": "INTERNAL_ERROR",
                "message": f"Error: {str(e)}"
            }, ensure_ascii=False) + "\n"

    async def chat_agent_stream(self, user_input: str) -> AsyncIterable[str]:
        try:
            yield json.dumps({
                "type": "status", 
                "message": "Answering..."
            }, ensure_ascii=False) + "\n"
            
            prompt = GENERAL_CHAT_PROMPT.format(user_input=user_input)
            
            for chunk_text in self.key_manager.stream_content(prompt, use_stream_config=True):
                if chunk_text:
                    data = json.dumps({
                        "type": "text", 
                        "content": chunk_text
                    }, ensure_ascii=False)
                    yield f"{data}\n"
                    
        except Exception as e:
            logger.error(f"Chat agent error: {e}")
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"

    def _get_history_string(self) -> str:
        if not self.memory_window:
            return "No chat history yet."
        return "\n".join([f"{m['role']}: {m['content']}" for m in self.memory_window])

    async def _refine_user_query(self, user_input: str) -> str:
        try:
            prompt = QUERY_REFINER_PROMPT.format(user_input=user_input)
            response = await asyncio.to_thread(self.key_manager.generate_content, prompt)
            refined_query = response.text.strip()
            logger.info(f"🔍 Refined Query: '{user_input}' -> '{refined_query}'")
            return refined_query
        except Exception as e:
            logger.error(f"Error refining query: {e}")
            return user_input

agent_system = HistoryAIAgent()