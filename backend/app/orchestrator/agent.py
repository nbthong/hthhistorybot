import os
from typing import AsyncIterable
import asyncio
import logging
import json

from app.services.key_manager_gemini import key_manager
from app.orchestrator.retriever import search_knowledge
from app.utils.prompts import (
    ORCHESTRATOR_INTENT_PROMPT,
    RAG_ANSWER_PROMPT,
    QUIZ_GENERATION_PROMPT,
    IMAGE_GENERATION_PROMPT,
    )
from app.utils.config import TEXT_GENERATION_CONFIG

logger = logging.getLogger(__name__)

if not key_manager:
    raise RuntimeError("Gemini API keys are not configured on the server.")


class HistoryAIAgent:
    def __init__(self) -> None:
        self.key_manager = key_manager

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

    async def orchestrator(self, user_input: str) -> str:
        if fast := self._infer_intent_fast(user_input):
            return fast

        prompt = ORCHESTRATOR_INTENT_PROMPT.format(user_input=user_input)
        response = self.key_manager.generate_content(prompt)
        return (response.text or "").strip().upper()

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
        knowledges = search_knowledge(user_input, use_hybrid=True)
        context_parts = [f"{k['content_text']}" for k in knowledges]
        context = "\n\n".join(context_parts)

        enable_image = (os.getenv("ENABLE_IMAGE_GENERATION", "0").strip() == "1")
        image_future = asyncio.create_task(self._generate_image_task(user_input, context)) if enable_image else None
        prompt = RAG_ANSWER_PROMPT.format(context=context, user_input=user_input)
        
        for chunk_text in self.key_manager.stream_content(prompt):
            if chunk_text:
                data = json.dumps({
                    "type": "text", 
                    "content": chunk_text
                }, ensure_ascii=False)
                yield f"{data}\n" 

        if image_future:
            image_result = await image_future
            if image_result:
                mime_type, image_base64 = image_result
                data = json.dumps(
                    {"type": "image", "mime_type": mime_type, "data": image_base64},
                    ensure_ascii=False,
                )
                yield f"{data}\n"


    async def quiz_agent_stream(self, user_input: str) -> AsyncIterable[str]:
        knowledges = search_knowledge(user_input, limit=3, use_hybrid=True)
        
        context_parts = []
        for k in knowledges:
            page_info = f"[Trang {k.get('page_id', '?')} - {k.get('topic', '')}]"
            context_parts.append(f"{page_info}\n{k['content_text']}")
        
        context = "\n\n---\n\n".join(context_parts)

        prompt = QUIZ_GENERATION_PROMPT.format(
            context=context,
            user_input=user_input,
        )
        
        for text in self.key_manager.stream_content(prompt):
            if text:
                data = json.dumps(
                    {"type": "text", "content": text},
                    ensure_ascii=False,
                )
                yield f"{data}\n"

agent_system = HistoryAIAgent()