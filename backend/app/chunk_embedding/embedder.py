import logging
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from services.key_manager_gemini import key_manager
from app.utils.config import GEMINI_EMBEDDING_MODEL, LOCAL_EMBEDDING_MODEL

logger = logging.getLogger(__name__)


class HybridEmbedder:
    def __init__(self) -> None:
        self.local_model = HuggingFaceEmbeddings(model_name=LOCAL_EMBEDDING_MODEL)
        logger.info("✅ Ready to use local embedding model.")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        try:
            current_key = key_manager.keys[key_manager.current_index]
            gemini_embedder = GoogleGenerativeAIEmbeddings(
                model=GEMINI_EMBEDDING_MODEL,
                google_api_key=current_key,
            )
            return gemini_embedder.embed_documents(texts)

        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                logger.warning("⚠️ Gemini Embedding quota exceeded, trying new key...")
                if key_manager.switch_key():
                    return self.embed_documents(texts)

            logger.error(f"❌ Gemini Embedding failed. Switching to LOCAL. Error: {e}")
            return self.local_model.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        try:
            current_key = key_manager.keys[key_manager.current_index]
            gemini_embedder = GoogleGenerativeAIEmbeddings(
                model=GEMINI_EMBEDDING_MODEL,
                google_api_key=current_key,
            )
            return gemini_embedder.embed_query(text)
        except Exception as e:
            logger.error(f"❌ Gemini Embedding query failed. Switching to LOCAL. Error: {e}")
            return self.local_model.embed_query(text)