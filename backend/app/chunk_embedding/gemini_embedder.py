from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Iterable, List, Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pymongo import UpdateOne

from app.chunk_embedding.chunking import chunk_text
from app.databases.vector_store import ensure_vector_indexes, get_vector_collection
from app.utils.config import (
    EMBED_BATCH_SIZE,
    ENV_FILE,
    MODEL_EMBEDDING,
    MONGO_BULK_WRITE_BATCH_SIZE,
)

logger = logging.getLogger(__name__)

load_dotenv(ENV_FILE)


def _iter_batches(items: List[str], batch_size: int) -> Iterable[List[str]]:
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]


def _extract_embedding_values(item: Any) -> Optional[List[float]]:
    if item is None:
        return None

    if isinstance(item, list) and item and all(isinstance(x, (int, float)) for x in item):
        return [float(x) for x in item]

    values = getattr(item, "values", None)
    if isinstance(values, list):
        return [float(x) for x in values]

    if isinstance(item, dict):
        v = item.get("values")
        if isinstance(v, list):
            return [float(x) for x in v]

    return None


def _extract_embeddings_from_response(resp: Any) -> List[List[float]]:
    if resp is None:
        return []

    # Common shape: resp.embeddings -> list[Embedding]
    embeddings = getattr(resp, "embeddings", None)
    if isinstance(embeddings, list):
        out: List[List[float]] = []
        for e in embeddings:
            vec = _extract_embedding_values(e)
            if vec:
                out.append(vec)
        return out

    # Sometimes: resp.embedding -> Embedding (single)
    embedding = getattr(resp, "embedding", None)
    vec = _extract_embedding_values(embedding)
    if vec:
        return [vec]

    # Last-resort: resp might already be list-like
    if isinstance(resp, list):
        out: List[List[float]] = []
        for e in resp:
            vec2 = _extract_embedding_values(e)
            if vec2:
                out.append(vec2)
        return out

    return []


class GeminiEmbedder:
    def __init__(self, *, api_key: Optional[str] = None, model_name: str = MODEL_EMBEDDING) -> None:
        self.model_name = model_name
        self.api_key = (api_key or os.getenv("GOOGLE_API_KEY", "")).strip()
        if not self.api_key:
            raise ValueError("Missing GOOGLE_API_KEY (required for Gemini embeddings).")
        self.client = genai.Client(api_key=self.api_key)

    def embed_documents(self, texts: List[str], *, task_type: str | None = None) -> List[List[float]]:
        if not texts:
            return []
        embed_config = None
        if task_type:
            try:
                embed_config = types.EmbedContentConfig(task_type=task_type)
            except Exception:
                embed_config = None

        try:
            if embed_config is not None:
                resp = self.client.models.embed_content(model=self.model_name, contents=texts, config=embed_config)
            else:
                resp = self.client.models.embed_content(model=self.model_name, contents=texts)
        except TypeError:
            if embed_config is not None:
                resp = self.client.models.embed_content(model=self.model_name, content=texts, config=embed_config)
            else:
                resp = self.client.models.embed_content(model=self.model_name, content=texts)

        vectors = _extract_embeddings_from_response(resp)
        if len(vectors) != len(texts):
            raise ValueError(f"Gemini embed_content mismatch: vectors={len(vectors)} texts={len(texts)}")
        return vectors

    def embed_query(self, text: str) -> List[float]:
        vecs = self.embed_documents([text], task_type="RETRIEVAL_QUERY")
        return vecs[0] if vecs else []


def embed_and_store_lessons_gemini(
    merged: Dict[str, Any],
    *,
    mongo_collection_name: str,
    embed_model_name: str = MODEL_EMBEDDING,
) -> None:
    lessons: List[Dict[str, Any]] = list(merged.get("lessons") or [])
    if not lessons:
        logger.warning("No lessons to embed.")
        return

    ensure_vector_indexes(mongo_collection_name)
    vector_col = get_vector_collection(mongo_collection_name)
    embedder = GeminiEmbedder(model_name=embed_model_name)

    logger.info(
        "Start Gemini embedding lessons=%s, model=%s, target_collection=%s",
        len(lessons),
        embed_model_name,
        mongo_collection_name,
    )

    processed_at = time.strftime("%Y-%m-%d %H:%M:%S")
    ops: List[UpdateOne] = []

    for lesson in lessons:
        lesson_key = str(lesson.get("lesson_key") or "")
        if not lesson_key:
            continue

        merged_text = str(lesson.get("merged_text") or "").strip()
        if len(merged_text) <= 20:
            continue

        chunks = [c for c in chunk_text(merged_text) if len(c.strip()) > 20]
        if not chunks:
            continue

        embedding_dim: int | None = None
        for text_batch in _iter_batches(chunks, EMBED_BATCH_SIZE):
            dense_vectors = embedder.embed_documents(text_batch, task_type="RETRIEVAL_DOCUMENT")

            if embedding_dim is None:
                embedding_dim = len(dense_vectors[0]) if dense_vectors else 0

            for i, dense_vec in enumerate(dense_vectors):
                vector_record: Dict[str, Any] = {
                    "doc_id": lesson_key,
                    "source": lesson.get("source"),
                    "chapter": lesson.get("chapter"),
                    "topic": lesson.get("topic"),
                    "page_ids": lesson.get("page_ids"),
                    "page_id": (lesson.get("page_ids") or [None])[0],
                    "doc_ids": lesson.get("doc_ids"),
                    "lesson_label": lesson.get("lesson_label"),
                    "lesson_number": lesson.get("lesson_number"),
                    "content_text": text_batch[i],
                    "content_type": "lesson",
                    "embedding_vector": dense_vec,
                    "embedding_model": embed_model_name,
                    "embedding_dim": embedding_dim,
                    "processed_at": processed_at,
                }

                query = {"doc_id": lesson_key, "content_text": text_batch[i]}
                ops.append(UpdateOne(query, {"$set": vector_record}, upsert=True))

                if len(ops) >= MONGO_BULK_WRITE_BATCH_SIZE:
                    vector_col.bulk_write(ops, ordered=False)
                    ops.clear()

    if ops:
        vector_col.bulk_write(ops, ordered=False)

    logger.info("Gemini embedding lessons completed.")


