from typing import AsyncIterable

from app.services.key_manager_gemini import key_manager
from app.orchestrator.retriever import search_knowledge
from app.utils.prompts import (
    ORCHESTRATOR_INTENT_PROMPT,
    RAG_ANSWER_PROMPT,
    QUIZ_GENERATION_PROMPT,
)

if not key_manager:
    raise RuntimeError("Gemini API keys are not configured on the server.")


class HistoryAIAgent:
    def __init__(self) -> None:
        self.key_manager = key_manager

    async def orchestrator(self, user_input: str) -> str:
        prompt: str = ORCHESTRATOR_INTENT_PROMPT.format(user_input=user_input)
        response = self.key_manager.generate_content(prompt)
        intent: str = response.text.strip().upper()
        return intent

    async def rag_agent_stream(self, user_input: str) -> AsyncIterable[str]:
        knowledges = search_knowledge(user_input, use_hybrid=True)
        
        # Format context with metadata (page_id, chapter, topic) to LLM quote
        context_parts = []
        for k in knowledges:
            page_info = f"[Trang {k.get('page_id', '?')} - {k.get('chapter', '')} - {k.get('topic', '')}]"
            context_parts.append(f"{page_info}\n{k['content_text']}")
        
        context = "\n\n---\n\n".join(context_parts)

        prompt = RAG_ANSWER_PROMPT.format(
            context=context,
            user_input=user_input,
        )

        for text in self.key_manager.stream_content(prompt):
            yield text

    async def quiz_agent_stream(self, user_input: str) -> AsyncIterable[str]:
        knowledges = search_knowledge(user_input, limit=3, use_hybrid=True)
        
        # Format context với metadata
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
            yield text


agent_system = HistoryAIAgent()