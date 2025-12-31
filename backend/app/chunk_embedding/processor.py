import logging
import time
from typing import Any, Dict, List

from app.databases.database import get_database
from app.chunk_embedding.embedder import HybridEmbedder
from app.utils.config import MONGO_VECTOR_COLLECTION, MONGO_COLLECTION_NAME

logger = logging.getLogger(__name__)


def process_and_store_vectors() -> None:
    db = get_database()
    source_col = db[MONGO_COLLECTION_NAME]
    vector_col = db[MONGO_VECTOR_COLLECTION]

    raw_data: List[Dict[str, Any]] = list(source_col.find({}))
    if not raw_data:
        logger.error("❌ No data found in MongoDB. Please run extract_pdf.py first!")
        return

    embedder = HybridEmbedder()

    print(f"Starting embedding process for {len(raw_data)} pages...")

    for record in raw_data:
        page_id: int = record["page_id"]
        source: str = record["source"]
        page_data: Dict[str, Any] = record["data"]

        chunks_to_embed: List[Dict[str, str]] = []

        for seg in page_data.get("content_segments", []):
            text = (
                f"{seg.get('heading', '')}\n"
                f"{seg.get('text', '')}\n"
                f"{seg.get('table_markdown', '') or ''}"
            )
            if len(text.strip()) <= 20:
                continue

            existing_chunk = vector_col.find_one(
                {
                    "doc_id": record["doc_id"],
                    "content_text": text,
                }
            )
            if existing_chunk:
                continue

            chunks_to_embed.append({"text": text, "type": "text"})

        # get from visual analysis
        for vis in page_data.get("visual_analysis", []):
            desc = vis.get("description", "")
            if desc:
                visual_text: str = f"[Hình ảnh]: {desc}"

                existing_visual = vector_col.find_one(
                    {
                        "doc_id": record["doc_id"],
                        "content_text": visual_text,
                    }
                )
                if existing_visual:
                    continue

                chunks_to_embed.append(
                    {"text": visual_text, "type": "visual"}
                )

        if not chunks_to_embed:
            continue

        print(f"   🔄 Embedding {len(chunks_to_embed)} segments of page {page_id}...")

        # perform embedding
        texts: List[str] = [c["text"] for c in chunks_to_embed]
        vectors = embedder.embed_documents(texts)
        if len(vectors) != len(texts):
            raise ValueError(
                f"Embedding output mismatch: vectors={len(vectors)} texts={len(texts)}"
            )
        embedding_dim: int = len(vectors[0]) if vectors else 0

        # save to MongoDB
        for i, vector in enumerate(vectors):
            vector_record: Dict[str, Any] = {
                "doc_id": record["doc_id"],
                "page_id": page_id,
                "source": source,
                "chapter": page_data["page_info"]["chapter"],
                "topic": page_data["page_info"]["topic"],
                "content_text": chunks_to_embed[i]["text"],
                "content_type": chunks_to_embed[i]["type"],
                "embedding_vector": vector,
                "embedding_model": getattr(embedder, "model_name", "unknown"),
                "embedding_dim": embedding_dim,
                "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }

            query = {
                "doc_id": record["doc_id"],
                "content_text": chunks_to_embed[i]["text"],
            }
            vector_col.update_one(query, {"$set": vector_record}, upsert=True)

        print(f"Saved vectors for page {page_id} to MongoDB Cloud.")
        time.sleep(1) 
    print("All knowledge and vectors are now in MongoDB.")


if __name__ == "__main__":
    process_and_store_vectors()