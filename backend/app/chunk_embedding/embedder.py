import logging
from typing import List, Optional, Dict, Any
from FlagEmbedding import BGEM3FlagModel

from app.utils.config import LOCAL_EMBEDDING_MODEL

logger = logging.getLogger(__name__)


class HybridEmbedder:

    def __init__(self, use_sparse: bool = True, use_colbert: bool = False) -> None:
        self.model_name: str = LOCAL_EMBEDDING_MODEL
        self._model: Optional[BGEM3FlagModel] = None
        self.use_sparse = use_sparse
        self.use_colbert = use_colbert
        logger.info(f"Initializing HybridEmbedder: sparse={use_sparse}, colbert={use_colbert}")

    def _get_model(self) -> BGEM3FlagModel:
        if self._model is None:
            logger.info(f"Loading BGE-M3 model: {self.model_name} with fp16=True")
            self._model = BGEM3FlagModel(self.model_name, use_fp16=True)
        return self._model

    def embed_documents(
        self, 
        texts: list[str],
        return_dense: bool = True,
        return_sparse: bool = None,
        return_colbert: bool = None
    ) -> list[list[float]] | Dict[str, Any]:
        if not texts:
            return []

        if return_sparse is None:
            return_sparse = self.use_sparse
        if return_colbert is None:
            return_colbert = self.use_colbert

        try:
            model = self._get_model()
            output = model.encode(
                texts, 
                batch_size=12, 
                max_length=8192,
                return_dense=return_dense,
                return_sparse=return_sparse,
                return_colbert_vecs=return_colbert
            )

            if return_dense and not return_sparse and not return_colbert:
                dense_vecs = output["dense_vecs"]
                if hasattr(dense_vecs, "tolist"):
                    return dense_vecs.tolist()
                
                vectors: List[List[float]] = []
                for v in dense_vecs:
                    vectors.append([float(x) for x in v])
                return vectors
            
            result = {}
            if return_dense:
                dense_vecs = output["dense_vecs"]
                if hasattr(dense_vecs, "tolist"):
                    result["dense_vecs"] = dense_vecs.tolist()
                else:
                    result["dense_vecs"] = [[float(x) for x in v] for v in dense_vecs]
            
            if return_sparse and "lexical_weights" in output:
                result["lexical_weights"] = output["lexical_weights"]
            
            if return_colbert and "colbert_vecs" in output:
                result["colbert_vecs"] = output["colbert_vecs"]
            
            return result

        except Exception as e:
            logger.exception("❌ BGE-M3 embedding failed: %s", e)
            raise

    def embed_query(self, text: str) -> list[float]:
        result = self.embed_documents([text], return_dense=True, return_sparse=False, return_colbert=False)
        if isinstance(result, list) and len(result) > 0:
            return result[0]
        return []
    
    def compute_lexical_score(self, query_weights: Dict, doc_weights: Dict) -> float:
        model = self._get_model()
        return model.compute_lexical_matching_score(query_weights, doc_weights)