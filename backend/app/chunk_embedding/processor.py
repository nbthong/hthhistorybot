import logging
from pathlib import Path
from typing import Any, Dict

from app.chunk_embedding.preprocessing import run as preprocess_run
from app.chunk_embedding.embedder import embed_and_store_lessons
from app.utils.config import OUTPUT_JSON_CHUNK_EMBEDDING, MONGO_VECTOR_COLLECTION, OUTPUT_JSON_DATA

logger = logging.getLogger(__name__)


def run(
    *,
    history_db_path: str | Path = OUTPUT_JSON_DATA,
    merge_output_path: str | Path = OUTPUT_JSON_CHUNK_EMBEDDING,
    include_non_content_pages: bool = False,
    mongo_vector_collection_name: str = MONGO_VECTOR_COLLECTION,
) -> Dict[str, Any]:
    merged = preprocess_run(
        history_db_path=history_db_path,
        merge_output_path=merge_output_path,
        include_non_content_pages=include_non_content_pages,
    )

    embed_and_store_lessons(merged, mongo_collection_name=mongo_vector_collection_name)
    return merged


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run(include_non_content_pages=False)