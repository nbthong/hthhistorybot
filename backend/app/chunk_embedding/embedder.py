import logging
from typing import List, Optional
from FlagEmbedding import BGEM3FlagModel

from app.utils.config import LOCAL_EMBEDDING_MODEL

logger = logging.getLogger(__name__)


class HybridEmbedder:
    def __init__(self) -> None:
        self.model_name: str = LOCAL_EMBEDDING_MODEL
        self._model: Optional[BGEM3FlagModel] = None

    def _get_model(self) -> BGEM3FlagModel:
        if self._model is None:
            use_fp16=True # speed up computation with a slight performance degradation
            self._model = BGEM3FlagModel(self.model_name, use_fp16=True)
        return self._model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        try:
            model = self._get_model()
            output = model.encode(texts, batch_size=12, max_length=8192)
            dense_vecs = output["dense_vecs"]

            if hasattr(dense_vecs, "tolist"):
                return dense_vecs.tolist()  

            vectors: List[List[float]] = []
            for v in dense_vecs:
                vectors.append([float(x) for x in v])
            return vectors

        except Exception as e:
            logger.exception("❌ BGE-M3 embedding failed: %s", e)
            raise

    def embed_query(self, text: str) -> list[float]:
        vectors = self.embed_documents([text])
        return vectors[0] if vectors else []