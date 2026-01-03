import logging
import time
from typing import Any, Dict, List

from app.databases.database import get_database
from app.chunk_embedding.embedder import HybridEmbedder
from app.utils.config import (
    MONGO_VECTOR_COLLECTION,
    MONGO_COLLECTION_NAME,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    USE_SPARSE_EMBEDDING,
    USE_COLBERT_EMBEDDING,
)

logger = logging.getLogger(__name__)


def chunk_text(text: str) -> List[str]:
    normalized = " ".join(text.split())
    if len(normalized) <= CHUNK_SIZE:
        return [normalized]

    chunks: List[str] = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + CHUNK_SIZE)
        chunk = normalized[start:end]
        chunks.append(chunk)
        if end == len(normalized):
            break
        start = max(0, end - CHUNK_OVERLAP)
    return chunks


def process_and_store_vectors() -> None:
    db = get_database()
    source_col = db[MONGO_COLLECTION_NAME]
    vector_col = db[MONGO_VECTOR_COLLECTION]

    raw_data: List[Dict[str, Any]] = list(source_col.find({}))
    if not raw_data:
        logger.error("❌ No data found in MongoDB. Please run extract_pdf.py first!")
        return

    embedder = HybridEmbedder(
        use_sparse=USE_SPARSE_EMBEDDING,
        use_colbert=USE_COLBERT_EMBEDDING
    )

    print(f"🚀 Starting embedding process for {len(raw_data)} pages...")
    print(f"   Sparse: {USE_SPARSE_EMBEDDING}, ColBERT: {USE_COLBERT_EMBEDDING}")

    for record in raw_data:
        page_id: int = record["page_id"]
        source: str = record["source"]
        page_data: Dict[str, Any] = record["data"]

        chunks_to_embed: List[Dict[str, str]] = []

        for seg in page_data.get("content_segments", []):
            base_text = (
                f"{seg.get('heading', '')}\n"
                f"{seg.get('text', '')}\n"
                f"{seg.get('table_markdown', '') or ''}"
            )
            if len(base_text.strip()) <= 20:
                continue

            for chunk in chunk_text(base_text):
                if len(chunk.strip()) <= 20:
                    continue
                existing_chunk = vector_col.find_one(
                    {
                        "doc_id": record["doc_id"],
                        "content_text": chunk,
                    }
                )
                if existing_chunk:
                    continue
                chunks_to_embed.append({"text": chunk, "type": "text"})

        # get from visual analysis
        for vis in page_data.get("visual_analysis", []):
            desc = vis.get("description", "")
            if desc:
                visual_text: str = f"[Hình ảnh]: {desc}"
                for chunk in chunk_text(visual_text):
                    if len(chunk.strip()) <= 20:
                        continue
                    existing_visual = vector_col.find_one(
                        {
                            "doc_id": record["doc_id"],
                            "content_text": chunk,
                        }
                    )
                    if existing_visual:
                        continue

                    chunks_to_embed.append(
                        {"text": chunk, "type": "visual"}
                    )

        if not chunks_to_embed:
            continue

        print(f"   🔄 Embedding {len(chunks_to_embed)} segments of page {page_id}...")

        # perform embedding (dense + sparse nếu bật)
        texts: List[str] = [c["text"] for c in chunks_to_embed]
        embedding_output = embedder.embed_documents(
            texts,
            return_dense=True,
            return_sparse=USE_SPARSE_EMBEDDING,
            return_colbert=False 
        )
        
        if isinstance(embedding_output, dict):
            dense_vectors = embedding_output["dense_vecs"]
            sparse_weights = embedding_output.get("lexical_weights", None)
        else:
            dense_vectors = embedding_output
            sparse_weights = None
        
        if len(dense_vectors) != len(texts):
            raise ValueError(
                f"Embedding output mismatch: vectors={len(dense_vectors)} texts={len(texts)}"
            )
        embedding_dim: int = len(dense_vectors[0]) if dense_vectors else 0

        # save to MongoDB
        for i, dense_vec in enumerate(dense_vectors):
            vector_record: Dict[str, Any] = {
                "doc_id": record["doc_id"],
                "page_id": page_id,
                "source": source,
                "chapter": page_data["page_info"]["chapter"],
                "topic": page_data["page_info"]["topic"],
                "content_text": chunks_to_embed[i]["text"],
                "content_type": chunks_to_embed[i]["type"],
                "embedding_vector": dense_vec,
                "embedding_model": getattr(embedder, "model_name", "unknown"),
                "embedding_dim": embedding_dim,
                "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            
            if sparse_weights and i < len(sparse_weights):
                try:
                    lexical = sparse_weights[i]
                    if isinstance(lexical, dict):
                        sorted_tokens = sorted(lexical.items(), key=lambda x: abs(x[1]), reverse=True)[:100]
                        vector_record["lexical_weights"] = dict(sorted_tokens)
                    else:
                        logger.warning(f"Lexical weights không phải dict: {type(lexical)}")
                except Exception as e:
                    logger.warning(f"Failed to process lexical weights for chunk {i}: {e}")

            query = {
                "doc_id": record["doc_id"],
                "content_text": chunks_to_embed[i]["text"],
            }
            
            try:
                vector_col.update_one(query, {"$set": vector_record}, upsert=True)
            except Exception as e:
                logger.error(f"Failed to save vector for page {page_id}, chunk {i}: {e}")
                if "lexical_weights" in vector_record:
                    logger.info(f"Retrying without lexical_weights...")
                    vector_record_no_sparse = {k: v for k, v in vector_record.items() if k != "lexical_weights"}
                    try:
                        vector_col.update_one(query, {"$set": vector_record_no_sparse}, upsert=True)
                        logger.info(f"Saved without lexical_weights")
                    except Exception as e2:
                        logger.error(f"Still failed: {e2}")
                        raise

        print(f"Saved vectors for page {page_id} to MongoDB Cloud.")
        time.sleep(1) 
    print("All knowledge and vectors are now in MongoDB.")


if __name__ == "__main__":
    process_and_store_vectors()