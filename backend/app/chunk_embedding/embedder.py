import logging
import time
import threading
from typing import List, Optional, Dict, Any, Iterable, Set, Tuple
from FlagEmbedding import BGEM3FlagModel
from pymongo import UpdateOne

from app.utils.config import (
    LOCAL_EMBEDDING_MODEL,
    USE_SPARSE_EMBEDDING,
    USE_COLBERT_EMBEDDING,
    MONGO_VECTOR_COLLECTION,
    OUTPUT_JSON_CHUNK_EMBEDDING,
    EMBED_BATCH_SIZE,
    MONGO_BULK_WRITE_BATCH_SIZE,
)
from app.databases.vector_store import get_vector_collection
from app.chunk_embedding.chunking import chunk_text

logger = logging.getLogger(__name__)

# Global singleton instance và lock để thread-safe
_embedder_instance: Optional["HybridEmbedder"] = None
_embedder_lock = threading.Lock()

_LEXICAL_TOP_K = 100
_EXISTING_LOOKUP_BATCH = 500


def _iter_batches(items: List[str], batch_size: int) -> Iterable[List[str]]:
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]

def _existing_chunks_for_doc(vector_col,*,doc_id: str,chunks: List[str],) -> Set[str]:
    if not chunks:
        return set()

    existing: Set[str] = set()
    for batch in _iter_batches(chunks, _EXISTING_LOOKUP_BATCH):
        cursor = vector_col.find(
            {"doc_id": doc_id, "content_text": {"$in": batch}},
            {"_id": 0, "content_text": 1},
        )
        for d in cursor:
            ct = d.get("content_text")
            if isinstance(ct, str) and ct:
                existing.add(ct)
    return existing

def _extract_dense_and_sparse(
    embedding_output: list[list[float]] | Dict[str, Any],
) -> Tuple[List[List[float]], List[Dict[str, float]] | None]:
    if isinstance(embedding_output, dict):
        dense_vectors = embedding_output.get("dense_vecs") or []
        sparse_weights = embedding_output.get("lexical_weights")
        return dense_vectors, sparse_weights
    return embedding_output, None

def _topk_lexical_weights(lexical: Any, top_k: int = _LEXICAL_TOP_K) -> Dict[str, float] | None:
    if not isinstance(lexical, dict):
        return None
    sorted_tokens = sorted(lexical.items(), key=lambda x: abs(x[1]), reverse=True)[:top_k]
    # Convert numpy types to Python native types for JSON serialization
    return {str(k): float(v) for k, v in sorted_tokens}


class HybridEmbedder:

    def __init__(self, use_sparse: bool = True, use_colbert: bool = False) -> None:
        self.model_name: str = LOCAL_EMBEDDING_MODEL
        self._model: Optional[BGEM3FlagModel] = None
        self._model_lock = threading.Lock() 
        self.use_sparse = use_sparse
        self.use_colbert = use_colbert
        logger.info(f"Initializing HybridEmbedder: sparse={use_sparse}, colbert={use_colbert}")

    def _get_model(self) -> BGEM3FlagModel:
        # Double-check locking pattern để đảm bảo thread-safe
        if self._model is None:
            with self._model_lock:
                # Check lại sau khi acquire lock (có thể thread khác đã load xong)
                if self._model is None:
                    try:
                        logger.info(f"Loading BGE-M3 model: {self.model_name} with fp16=True")
                        self._model = BGEM3FlagModel(self.model_name, use_fp16=True)
                        logger.info("✅ BGE-M3 model loaded successfully")
                    except MemoryError as e:
                        logger.error(f"❌ MemoryError loading BGE-M3 model: {e}")
                        logger.error("💡 Tip: Restart server or increase available RAM")
                        raise
                    except Exception as e:
                        logger.error(f"❌ Failed to load BGE-M3 model: {e}")
                        raise
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

def get_embedder(use_sparse: bool = None, use_colbert: bool = None) -> HybridEmbedder:
    """
    Singleton pattern: trả về global embedder instance (thread-safe).
    Chỉ load model 1 lần cho toàn app, reuse cho tất cả requests.
    """
    global _embedder_instance, _embedder_lock
    
    if use_sparse is None:
        use_sparse = USE_SPARSE_EMBEDDING
    if use_colbert is None:
        use_colbert = USE_COLBERT_EMBEDDING
    
    if _embedder_instance is None:
        with _embedder_lock:
            # Double-check locking
            if _embedder_instance is None:
                _embedder_instance = HybridEmbedder(
                    use_sparse=use_sparse,
                    use_colbert=use_colbert,
                )
    return _embedder_instance


def embed_and_store_lessons(
    merged: Dict[str, Any],
    *,
    mongo_collection_name: str = MONGO_VECTOR_COLLECTION,
) -> None:

    lessons: List[Dict[str, Any]] = list(merged.get("lessons") or [])
    if not lessons:
        logger.warning("No lessons to embed.")
        return

    vector_col = get_vector_collection(mongo_collection_name)

    # Dùng singleton embedder
    embedder = get_embedder(
        use_sparse=USE_SPARSE_EMBEDDING,
        use_colbert=USE_COLBERT_EMBEDDING,
    )

    logger.info(
        "Start embedding lessons=%s, sparse=%s, colbert=%s, target_collection=%s",
        len(lessons),
        USE_SPARSE_EMBEDDING,
        USE_COLBERT_EMBEDDING,
        mongo_collection_name,
    )

    for lesson in lessons:
        lesson_key = str(lesson.get("lesson_key") or "")
        if not lesson_key:
            continue

        merged_text = str(lesson.get("merged_text") or "").strip()
        if len(merged_text) <= 20:
            continue

        # Chunk merged_text
        chunks = [c for c in chunk_text(merged_text) if len(c.strip()) > 20]
        if not chunks:
            continue

        existing = _existing_chunks_for_doc(vector_col, doc_id=lesson_key, chunks=chunks)
        chunks_to_embed = [c for c in chunks if c not in existing]

        if not chunks_to_embed:
            continue

        embedding_dim: int | None = None
        processed_at = time.strftime("%Y-%m-%d %H:%M:%S")

        # Embed by batch to reduce peak RAM/VRAM when lessons/chunks are large
        ops: List[UpdateOne] = []
        for text_batch in _iter_batches(chunks_to_embed, EMBED_BATCH_SIZE):
            embedding_output = embedder.embed_documents(
                text_batch,
                return_dense=True,
                return_sparse=USE_SPARSE_EMBEDDING,
                return_colbert=False,
            )
            dense_vectors, sparse_weights = _extract_dense_and_sparse(embedding_output)

            if len(dense_vectors) != len(text_batch):
                raise ValueError(
                    f"Embedding output mismatch: vectors={len(dense_vectors)} texts={len(text_batch)}"
                )

            if embedding_dim is None:
                embedding_dim = len(dense_vectors[0]) if dense_vectors else 0

            for i, dense_vec in enumerate(dense_vectors):
                vector_record: Dict[str, Any] = {
                    "doc_id": lesson_key,
                    "source": lesson.get("source"),
                    "chapter": lesson.get("chapter"),
                    "topic": lesson.get("topic"),
                    "lesson_label": lesson.get("lesson_label"),
                    "lesson_number": lesson.get("lesson_number"),
                    "page_ids": lesson.get("page_ids"),
                    "doc_ids": lesson.get("doc_ids"),
                    "content_text": text_batch[i],
                    "content_type": "lesson",
                    "embedding_vector": dense_vec,
                    "embedding_model": getattr(embedder, "model_name", "unknown"),
                    "embedding_dim": embedding_dim,
                    "processed_at": processed_at,
                }

                if sparse_weights and i < len(sparse_weights):
                    lw = _topk_lexical_weights(sparse_weights[i])
                    if lw:
                        vector_record["lexical_weights"] = lw

                query = {"doc_id": lesson_key, "content_text": text_batch[i]}
                ops.append(UpdateOne(query, {"$set": vector_record}, upsert=True))

                if len(ops) >= MONGO_BULK_WRITE_BATCH_SIZE:
                    _flush_bulk_ops(vector_col, ops, lesson_key=lesson_key)
                    ops.clear()

        if ops:
            _flush_bulk_ops(vector_col, ops, lesson_key=lesson_key)

    logger.info("Embedding lessons completed.")

def _flush_bulk_ops(vector_col, ops, *, lesson_key: str) -> None:
    from pymongo.errors import BulkWriteError

    try:
        vector_col.bulk_write(ops, ordered=False)
    except BulkWriteError as e:
        logger.warning(
            "bulk_write failed (possibly due to duplicate key/race). lesson=%s details=%s",
            lesson_key,
            getattr(e, "details", None),
        )
    except Exception as e:
        logger.error("bulk_write failed lesson=%s: %s", lesson_key, e)
        for op in ops:
            try:
                vector_col.update_one(op._filter, op._doc, upsert=True)
            except Exception:
                try:
                    set_doc = (op._doc or {}).get("$set", {})  
                    if "lexical_weights" in set_doc:
                        set_doc = {k: v for k, v in set_doc.items() if k != "lexical_weights"}
                        vector_col.update_one(op._filter, {"$set": set_doc}, upsert=True) 
                except Exception as e2:
                    logger.error("Fallback update_one still error lesson=%s: %s", lesson_key, e2)

if __name__ == "__main__":
    import json
    
    logging.basicConfig(level=logging.INFO)
    
    # Read merged lessons from file
    merge_file = OUTPUT_JSON_CHUNK_EMBEDDING
    if not merge_file.exists():
        logger.error(f"File {OUTPUT_JSON_CHUNK_EMBEDDING} does not exist: {merge_file}")
        logger.info(f"Run preprocessing.py before to create {OUTPUT_JSON_CHUNK_EMBEDDING}")
        exit(1)
    
    with open(OUTPUT_JSON_CHUNK_EMBEDDING, "r", encoding="utf-8") as f:
        merged = json.load(f)
    
    # Embed and save to MongoDB
    embed_and_store_lessons(merged, mongo_collection_name=MONGO_VECTOR_COLLECTION)