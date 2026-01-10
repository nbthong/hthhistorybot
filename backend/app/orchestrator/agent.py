import os
from typing import AsyncIterable
import asyncio
import logging
import json
from collections import deque
from typing import List, Dict, Optional

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
from app.databases.database import get_history_from_mongo, save_message_to_mongo
from app.utils.config import LIMIT_WORD_COUNT_GENERATE_IMAGE

logger = logging.getLogger(__name__)

class HistoryAIAgent:
    def __init__(self) -> None:
        self.key_manager = key_manager
        self.sessions_memory: Dict[str, deque] = {}

    def _get_session_memory(self, session_id: str) -> deque:
        if session_id not in self.sessions_memory:
            self.sessions_memory[session_id] = deque(maxlen=6)
        return self.sessions_memory[session_id] 
    
    @staticmethod
    def _is_image_history_item(item: Dict) -> bool:
        if not isinstance(item, dict):
            return False
        if item.get("message_type") == "image":
            return True
        if item.get("image") is not None:
            return True
        content = str(item.get("content") or "")
        return "<img" in content.lower()

    async def _get_unified_history(self, session_id: str, user_id: Optional[str] = None) -> str:
        if user_id:
            hist = await asyncio.to_thread(get_history_from_mongo, user_id, session_id, 6)
            if not hist: return ""
            text_hist = [h for h in hist if not self._is_image_history_item(h)]
            return "\n".join([f"{'Học sinh' if h.get('role')=='user' else 'Giáo viên'}: {h.get('content','')}" for h in text_hist])
        
        mem = self._get_session_memory(session_id)
        if not mem: return ""
        text_mem = [m for m in mem if not self._is_image_history_item(m)]
        return "\n".join([f"{m.get('role')}: {m.get('content')}" for m in text_mem])

    async def orchestrator(self, user_input: str, session_id: str, user_id: Optional[str] = None) -> str:
        history_str = await self._get_unified_history(session_id, user_id)
        prompt = ORCHESTRATOR_INTENT_PROMPT.format(user_input=user_input, history_str=history_str)
        response = self.key_manager.generate_content(prompt)
        intent = response.text.strip().upper()
        if "QUIZ" in intent: return "QUIZ"
        if "CHAT" in intent: return "CHAT"
        return "LEARN"

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

    async def _condense_question_advanced(self, user_input: str, history_str: str) -> str:
        if not history_str or history_str == "": return user_input
        prompt = CONDENSE_PROMPT.format(history_str=history_str, user_input=user_input)
        res = await asyncio.to_thread(self.key_manager.generate_content, prompt)
        return res.text.strip()

    def _get_history_string(self, session_id: str = "default_user") -> str:
        mem = self._get_session_memory(session_id)
        if not mem:
            return "Chưa có lịch sử trò chuyện."
        return "\n".join([f"{m['role']}: {m['content']}" for m in mem])

    async def rag_agent_stream(self, user_input: str, session_id: str = "default_user", user_id: Optional[str] = None) -> AsyncIterable[str]:
        try:
            yield json.dumps({"type": "status", "message": "🔍 Thầy đang tìm tài liệu cho em..."}, ensure_ascii=False) + "\n"
            history_str = await self._get_unified_history(session_id, user_id)
            search_query = await self._condense_question_advanced(user_input, history_str)
            clean_query = await self._refine_user_query(search_query)
            image_keywords = ["trận chiến", "diễn biến", "cuộc chiến", "diễn ra", "chiến dịch", "khởi nghĩa", "trận đánh", ]
            force_gen_image = any(k in clean_query.lower() for k in image_keywords)
            knowledges = await asyncio.to_thread(search_knowledge, search_query, limit=15, use_hybrid=True)

            if not knowledges:
                knowledges = await asyncio.to_thread(search_knowledge, user_input, limit=10)
                yield json.dumps({"type": "text", "content": "🔍 Thầy không tìm thấy tư liệu này."}, ensure_ascii=False) + "\n"
                return

            best_docs = await self._rerank_knowledge(search_query, knowledges)
            context = "\n---\n".join([f"[Trang {d.get('page_id')}]: {d['content_text']}" for d in best_docs])

            prompt = RAG_ANSWER_PROMPT.format(context=context, chat_history=history_str, user_input=user_input)

            full_response = ""
            for chunk_text in self.key_manager.stream_content(prompt, use_stream_config=True):
                if chunk_text:
                    full_response += chunk_text
                    yield json.dumps({"type": "text", "content": chunk_text}, ensure_ascii=False) + "\n"

            word_count = len(full_response.split())
            
            should_gen_image = force_gen_image or (word_count > LIMIT_WORD_COUNT_GENERATE_IMAGE)

            final_image_data = None 
            image_html: str | None = None
            if should_gen_image and os.getenv("ENABLE_IMAGE_GENERATION") == "1":
                yield json.dumps({
                    "type": "status", 
                    "message": "🖼️ Bài giảng dài và sinh động nên thầy đang vẽ hình minh họa cho em..." if word_count > LIMIT_WORD_COUNT_GENERATE_IMAGE else "🖼️ Thầy đang tạo hình ảnh minh họa cho diễn biến này..."
                }, ensure_ascii=False) + "\n"
                
                image_result = await self._generate_image_task(clean_query, context)
                
                if image_result:
                    mime_type, image_base64 = image_result
                    final_image_data = {"mime_type": mime_type, "data": image_base64}
                    # FE-friendly: chỉ cần render `content` là ra ảnh ngay
                    image_html = f'<img src="data:{mime_type};base64,{image_base64}" class="chat-image"/>'
                    yield json.dumps({
                        "type": "image", 
                        "mime_type": mime_type, 
                        "data": image_base64
                    }, ensure_ascii=False) + "\n"

            if user_id:
                await asyncio.to_thread(
                    save_message_to_mongo,
                    user_id, session_id, "user", user_input, None, "text"
                )
                await asyncio.to_thread(
                    save_message_to_mongo,
                    user_id, session_id, "assistant", full_response, None, "text"
                )
                # Lưu riêng 1 record cho ảnh (nếu có)
                if image_html and final_image_data:
                    await asyncio.to_thread(
                        save_message_to_mongo,
                        user_id, session_id, "assistant", image_html, final_image_data, "image"
                    )
            mem = self._get_session_memory(session_id)
            mem.append({"role": "Học sinh", "content": user_input, "message_type": "text"})
            mem.append({"role": "Giáo viên", "content": full_response, "message_type": "text"})
            if image_html:
                mem.append({"role": "Giáo viên", "content": image_html, "message_type": "image"})
        except Exception as e:
            logger.error(f"Error: {e}")
            yield json.dumps({"type": "error", "message": "System error."}, ensure_ascii=False) + "\n"

    async def quiz_agent_stream(self, user_input: str, session_id: str = "default_user", user_id: Optional[str] = None) -> AsyncIterable[str]:
        try:
            yield json.dumps({"type": "status", "message": "🔍 Thầy đang tìm tài liệu cho em..."}, ensure_ascii=False) + "\n"
            search_query = await self._condense_question_advanced(user_input, session_id)
            knowledges = await asyncio.to_thread(search_knowledge, search_query, limit=5, use_hybrid=True)

            context = "\n".join([k['content_text'] for k in knowledges])
            prompt = QUIZ_GENERATION_PROMPT.format(context=context, user_input=search_query)

            context = "\n\n".join([f"[Nguồn SGK]: {k['content_text']}" for k in knowledges])

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

            if user_id:
                await asyncio.to_thread(save_message_to_mongo, user_id, session_id, "user", f"Yêu cầu Quiz: {user_input}", None, "text")
                await asyncio.to_thread(save_message_to_mongo, user_id, session_id, "assistant", "[Bộ câu hỏi trắc nghiệm]", None, "text")
            
            mem = self._get_session_memory(session_id)
            mem.append({"role": "Học sinh", "content": user_input, "message_type": "text"})
            mem.append({"role": "Giáo viên", "content": "[Đã gửi bộ câu hỏi trắc nghiệm]", "message_type": "text"})

        except Exception as e:
            logger.error(f"Quiz agent error: {e}", exc_info=True)
            yield json.dumps({"type": "error", "message": f"Error generating quiz: {str(e)}"}, ensure_ascii=False) + "\n"

    async def chat_agent_stream(self, user_input: str, session_id: str = "default_user", user_id: Optional[str] = None) -> AsyncIterable[str]:
        try:
            yield json.dumps({"type": "status", "message": "🔍 Thầy đang trả lời câu hỏi cho em..."}, ensure_ascii=False) + "\n"
            
            prompt = GENERAL_CHAT_PROMPT.format(user_input=user_input)
            
            full_response = ""
            for chunk_text in self.key_manager.stream_content(prompt, use_stream_config=True):
                if chunk_text:
                    full_response += chunk_text
                    data = json.dumps({
                        "type": "text", 
                        "content": chunk_text
                    }, ensure_ascii=False)
                    yield f"{data}\n"

            if user_id:
                save_message_to_mongo(user_id, session_id, "user", user_input, None, "text")
                save_message_to_mongo(user_id, session_id, "assistant", full_response, None, "text")
            else:
                mem = self._get_session_memory(session_id)
                mem.append({"role": "Học sinh", "content": user_input, "message_type": "text"})
                mem.append({"role": "Giáo viên", "content": full_response, "message_type": "text"})
                    
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
            raw_ids = selected_data.get("selected_ids", [])
            selected_ids = []
            for val in raw_ids:
                try:
                    selected_ids.append(int(val))
                except (ValueError, TypeError):
                    continue
            
            filtered_knowledges = [knowledges[i] for i in selected_ids if i < len(knowledges)]
            return filtered_knowledges[:7] 
        except Exception as e:
            logger.error(f"Reranking error: {e}")
            return knowledges[:5] 

    def _get_context_memory(self, session_id: str, user_id: Optional[str]) -> str:
        if user_id:
            hist = get_history_from_mongo(user_id, session_id, limit=6)
            if not hist:
                return "Chưa có lịch sử trò chuyện."
            text_hist = [h for h in hist if not self._is_image_history_item(h)]
            return "\n".join([f"{'Học sinh' if h.get('role')=='user' else 'Giáo viên'}: {h.get('content','')}" for h in text_hist])
        else:
            return self._get_history_string(session_id)

agent_system = HistoryAIAgent()