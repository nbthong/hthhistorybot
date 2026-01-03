from __future__ import annotations

import logging
from typing import Any, Dict, List

from pymongo.collection import Collection

from app.databases.database import get_collection
from app.utils.config import (
    LOCAL_EMBEDDING_MODEL,
    MONGO_ATLAS_VECTOR_INDEX_NAME,
    MONGO_ATLAS_VECTOR_PATH,
    MONGO_VECTOR_COLLECTION_NEW,
    USE_EMBEDDING_MODEL_FILTER,
)

logger = logging.getLogger(__name__)


def get_vector_collection(name: str | None = None) -> Collection:
    return get_collection(name or MONGO_VECTOR_COLLECTION_NEW)


def ensure_vector_indexes(collection_name: str | None = None) -> None:
    vec = get_vector_collection(collection_name)
    try:
        vec.create_index([("doc_id", 1), ("content_text", 1)], unique=True)
    except Exception as e:
        logger.warning("Vector compound unique index may already exist: %s", e)
    try:
        vec.create_index("embedding_model")
    except Exception as e:
        logger.warning("Vector index 'embedding_model' may already exist: %s", e)
    try:
        vec.create_index([("content_text", "text")])
    except Exception as e:
        logger.warning("Vector text index on 'content_text' may already exist: %s", e)
    try:
        vec.create_index("page_id")
    except Exception as e:
        logger.warning("Vector index 'page_id' may already exist: %s", e)


def _is_filter_not_indexed_error(err: Exception) -> bool:
    msg = str(err) or ""
    return (
        ("needs to be indexed as filter" in msg.lower()) or 
        ("filter field" in msg.lower() and "index" in msg.lower())
    ) and ("embedding_model" in msg.lower())


def aggregate_vector_search_with_optional_filter(
    *,
    collection: Collection,
    query_vector: List[float],
    candidates: int,
    limit: int,
    project_stage: Dict[str, Any],
    embedding_model_filter: str | None = LOCAL_EMBEDDING_MODEL,
) -> List[Dict[str, Any]]:

    vector_search: Dict[str, Any] = {
        "index": MONGO_ATLAS_VECTOR_INDEX_NAME,
        "path": MONGO_ATLAS_VECTOR_PATH,
        "queryVector": query_vector,
        "numCandidates": candidates,
        "limit": limit,
    }
    # Only add filter if enabled in config and filter value provided
    if USE_EMBEDDING_MODEL_FILTER and embedding_model_filter:
        vector_search["filter"] = {"embedding_model": embedding_model_filter}

    pipeline = [{"$vectorSearch": vector_search}, {"$project": project_stage}]
    try:
        return list(collection.aggregate(pipeline))
    except Exception as e:
        if embedding_model_filter and _is_filter_not_indexed_error(e):
            logger.warning(
                "Atlas VectorSearch: Field 'embedding_model' is not indexed in Vector Search Index."
            )
            logger.warning(
                "Retrying without filter. To permanently fix, add 'embedding_model' to Vector Search Index "
                "in MongoDB Atlas UI (Search > Vector Search > Edit Index > Add filter field)."
            )
            vector_search.pop("filter", None)
            pipeline_retry = [{"$vectorSearch": vector_search}, {"$project": project_stage}]
            try:
                return list(collection.aggregate(pipeline_retry))
            except Exception as retry_err:
                logger.error(f"Retry without filter also failed: {retry_err}")
                raise
        raise


