import os
from typing import AsyncIterable
import asyncio
import logging
import json
from collections import deque
from typing import List, Dict

from app.services.key_manager_gemini import key_manager
from app.orchestrator.retriever import search_knowledge
from app.utils.prompts import (
    ORCHESTRATOR_INTENT_PROMPT,
    RAG_ANSWER_PROMPT,
    QUIZ_GENERATION_PROMPT,
    IMAGE_GENERATION_PROMPT,
    GENERAL_CHAT_PROMPT,
    QUERY_REFINER_PROMPT,
    RERANKER_PROMPT,
    CONDENSE_PROMPT,
)
from app.utils.config import LIMIT_WORD_COUNT_GENERATE_IMAGE

logger = logging.getLogger(__name__)

class HistoryAIAgent:
    def __init__(self) -> None:
        self.key_manager = key_manager
        self.memory_window = deque(maxlen=6) 
        self.sessions_memory: Dict[str, deque] = {}

    def _get_session_memory(self, session_id: str) -> deque:
        if session_id not in self.sessions_memory:
            self.sessions_memory[session_id] = deque(maxlen=6)
        return self.sessions_memory[session_id] 

    async def orchestrator(self, user_input: str) -> dict:
        prompt = ORCHESTRATOR_INTENT_PROMPT.format(user_input=user_input)
        response = self.key_manager.generate_content(prompt)
        return json.loads(response.text)

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

    async def _condense_question(self, user_input: str, session_id: str = "default_user") -> str:
        history_str = self._get_history_string(session_id)
        if not history_str:
            return user_input

        condense_prompt = CONDENSE_PROMPT.format(history_str=history_str, user_input=user_input)
        try:
            res = await asyncio.to_thread(self.key_manager.generate_content, condense_prompt)
            standalone_query = res.text.strip()
            logger.info(f"🔄 Context Logic: '{user_input}' -> '{standalone_query}'")
            return standalone_query
        except Exception:
            return user_input

    def _get_history_string(self, session_id: str = "default_user") -> str:
        mem = self._get_session_memory(session_id)
        if not mem:
            return "Chưa có lịch sử trò chuyện."
        return "\n".join([f"{m['role']}: {m['content']}" for m in mem])

    async def rag_agent_stream(self, user_input: str, session_id: str = "default_user") -> AsyncIterable[str]:
        try:
            yield json.dumps({"type": "status", "message": "🔍 Thầy đang tìm tài liệu cho em..."}, ensure_ascii=False) + "\n"
            history_str = self._get_history_string(session_id)
            search_query = await self._condense_question(user_input, session_id)
            clean_query = await self._refine_user_query(search_query)
            image_keywords = ["trận chiến", "diễn biến", "cuộc chiến", "diễn ra", "chiến dịch", "khởi nghĩa", "trận đánh", ]
            force_gen_image = any(k in clean_query.lower() for k in image_keywords)
            knowledges = await asyncio.to_thread(search_knowledge, clean_query, limit=15, use_hybrid=True)

            if not knowledges:
                yield json.dumps({"type": "text", "content": "🔍 Thầy không tìm thấy tư liệu này."}, ensure_ascii=False) + "\n"
                return

            best_docs = await self._rerank_knowledge(clean_query, knowledges)
            context = "\n\n---\n\n".join([f"[Trang {d.get('page_id')}]: {d['content_text']}" for d in best_docs])

            prompt = RAG_ANSWER_PROMPT.format(
                context=context,
                chat_history=history_str,
                user_input=user_input
            )

            full_response = ""
            for chunk_text in self.key_manager.stream_content(prompt, use_stream_config=True):
                if chunk_text:
                    full_response += chunk_text
                    yield json.dumps({"type": "text", "content": chunk_text}, ensure_ascii=False) + "\n"

            word_count = len(full_response.split())
            
            should_gen_image = force_gen_image or (word_count > LIMIT_WORD_COUNT_GENERATE_IMAGE)

            if should_gen_image and os.getenv("ENABLE_IMAGE_GENERATION") == "1":
                yield json.dumps({
                    "type": "status", 
                    "message": "🖼️ Bài giảng dài và sinh động nên thầy đang vẽ hình minh họa cho em..." if word_count > LIMIT_WORD_COUNT_GENERATE_IMAGE else "🖼️ Thầy đang tạo hình ảnh minh họa cho diễn biến này..."
                }, ensure_ascii=False) + "\n"
                
                image_result = await self._generate_image_task(clean_query, context)
                
                if image_result:
                    mime_type, image_base64 = image_result
                    yield json.dumps({
                        "type": "image", 
                        "mime_type": mime_type, 
                        "data": image_base64
                    }, ensure_ascii=False) + "\n"

            mem = self._get_session_memory(session_id)
            mem.append({"role": "Học sinh", "content": user_input})
            mem.append({"role": "Giáo viên", "content": full_response})

        except Exception as e:
            logger.error(f"Error: {e}")
            yield json.dumps({"type": "error", "message": "System error."}, ensure_ascii=False) + "\n"

    async def quiz_agent_stream(self, user_input: str) -> AsyncIterable[str]:
        try:
            yield json.dumps({"type": "status", "message": "🔍 Thầy đang tìm tài liệu cho em..."}, ensure_ascii=False) + "\n"
            search_query = await self._condense_question(user_input)

            knowledges = await asyncio.to_thread(
                search_knowledge, search_query, limit=5, use_hybrid=True
            )

            if not knowledges:
                yield json.dumps({"type": "error", "message": "🔍 Thầy không tìm thấy tài liệu này."}, ensure_ascii=False) + "\n"
                return

            context = "\n\n".join([f"[Trang {k.get('page_id')}]: {k['content_text']}" for k in knowledges])

            yield json.dumps({"type": "status", "message": "📝 Thầy đang tạo câu hỏi trắc nghiệm cho em..."}, ensure_ascii=False) + "\n"

            prompt = QUIZ_GENERATION_PROMPT.format(
                context=context,
                user_input=search_query
            )

            full_quiz_content = ""
            for text in self.key_manager.stream_content(prompt, use_stream_config=True):
                if text:
                    full_quiz_content += text
                    yield json.dumps({"type": "text", "content": text}, ensure_ascii=False) + "\n"
            
            self.memory_window.append({"role": "Học sinh", "content": f"Yêu cầu làm Quiz về {search_query}"})
            self.memory_window.append({"role": "Giáo viên", "content": "[Đã gửi bộ câu hỏi trắc nghiệm]"})

        except Exception as e:
            logger.error(f"Quiz agent error: {e}", exc_info=True)
            yield json.dumps({"type": "error", "message": f"Error generating quiz: {str(e)}"}, ensure_ascii=False) + "\n"

    async def chat_agent_stream(self, user_input: str, session_id: str = "default_user") -> AsyncIterable[str]:
        try:
            yield json.dumps({"type": "status", "message": "🔍 Thầy đang trả lời câu hỏi cho em..."}, ensure_ascii=False) + "\n"
            
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

    async def _rerank_knowledge(self, user_input: str, knowledges: List[Dict]) -> List[Dict]:
        if not knowledges:
            return []
            
        docs_for_ai = ""
        for i, k in enumerate(knowledges):
            docs_for_ai += f"ID {i}: {k['content_text'][:300]}...\n\n"

        prompt = RERANKER_PROMPT.format(user_input=user_input, documents=docs_for_ai)
        
        try:
            response = await asyncio.to_thread(self.key_manager.generate_content, prompt)
            selected_data = json.loads(response.text)
            selected_ids = selected_data.get("selected_ids", [])
            
            filtered_knowledges = [knowledges[i] for i in selected_ids if i < len(knowledges)]
            
            logger.info(f"Reranker: Giảm từ {len(knowledges)} đoạn xuống còn {len(filtered_knowledges)} đoạn chất lượng.")
            return filtered_knowledges[:3] 
        except Exception as e:
            logger.error(f"Reranking error: {e}")
            return knowledges[:3] 

agent_system = HistoryAIAgent()