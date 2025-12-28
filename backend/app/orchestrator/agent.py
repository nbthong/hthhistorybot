from typing import List, Dict, Any

from app.services.key_manager_gemini import key_manager
from app.orchestrator.retriever import search_knowledge
from app.utils.prompts import (
    ORCHESTRATOR_INTENT_PROMPT,
    RAG_ANSWER_PROMPT,
    QUIZ_GENERATION_PROMPT,
)

llm = key_manager.get_model()


class HistoryAIAgent:
    def __init__(self) -> None:
        self.llm = llm

    def orchestrator(self, user_input: str) -> str:
        prompt: str = ORCHESTRATOR_INTENT_PROMPT.format(user_input=user_input)
        intent: str = self.llm.generate_content(prompt).text.strip().upper()
        return intent

    def rag_agent(self, user_input: str) -> str:
        knowledges: List[Dict[str, Any]] = search_knowledge(user_input)
        context: str = "\n---\n".join([k["content_text"] for k in knowledges])

        prompt: str = RAG_ANSWER_PROMPT.format(
            context=context,
            user_input=user_input,
        )
        return self.llm.generate_content(prompt).text

    def quiz_agent(self, user_input: str) -> str:
        knowledges: List[Dict[str, Any]] = search_knowledge(user_input, limit=3)
        context: str = "\n---\n".join([k["content_text"] for k in knowledges])

        prompt: str = QUIZ_GENERATION_PROMPT.format(
            context=context,
            user_input=user_input,
        )
        return self.llm.generate_content(prompt).text


agent_system = HistoryAIAgent()