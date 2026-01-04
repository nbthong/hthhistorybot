from __future__ import annotations

import logging
import re
from typing import Any, Dict, List

from app.chunk_embedding.gemini_embedder import GeminiEmbedder
from app.databases.database import get_collection
from app.databases.vector_store import aggregate_vector_search_with_optional_filter
from app.utils.config import (
    MODEL_EMBEDDING,
    MONGO_VECTOR_COLLECTION_GEMINI,
    VECTOR_TOP_K,
    VECTOR_NUM_CANDIDATES,
    VECTOR_SCORE_THRESHOLD,
)

logger = logging.getLogger(__name__)

_embedder: GeminiEmbedder | None = None


def _get_embedder() -> GeminiEmbedder:
    global _embedder
    if _embedder is None:
        _embedder = GeminiEmbedder(model_name=MODEL_EMBEDDING)
    return _embedder


_VI_STOPWORDS = {
    # question/command words
    "so","sánh", "phan", "tích", "phân", "giải", "thích", "trình", "bày", "hãy", "cho", 
    "biết", "nêu", "kể", "tóm", "tắt", "làm", "rõ", "vì", "sao", "do", "đâu", "khi", "nào", 
    "ở", "đâu", "gì", "là", "như", "thế", "nào", "và", "hay", "hoặc", "của", "trong", "với",
    "theo", "đến", "từ", "một", "các", "những"
}


def _tokenize_vi(s: str) -> List[str]:
    s = (s or "").strip().lower()
    parts = re.split(r"[^0-9A-Za-zÀ-ỹ]+", s)
    return [p for p in parts if p]


def _build_fallback_terms(query: str, *, max_terms: int = 8) -> List[str]:
    raw_tokens = _tokenize_vi(query)
    if not raw_tokens:
        return []

    # Build bigrams from adjacent tokens (useful for Vietnamese multi-syllable words)
    bigrams: List[str] = []
    for i in range(len(raw_tokens) - 1):
        a, b = raw_tokens[i], raw_tokens[i + 1]
        if len(a) >= 2 and len(b) >= 2 and a not in _VI_STOPWORDS and b not in _VI_STOPWORDS:
            bigrams.append(f"{a} {b}")

    if bigrams:
        terms: List[str] = []
        for t in bigrams:
            if t not in terms:
                terms.append(t)
            if len(terms) >= max_terms:
                break
        return terms

    singles = [t for t in raw_tokens if len(t) >= 3 and t not in _VI_STOPWORDS]

    # Prefer bigrams first, then singles; keep uniqueness
    terms: List[str] = []
    for t in bigrams + singles:
        if t not in terms:
            terms.append(t)
        if len(terms) >= max_terms:
            break
    return terms


def _regex_fallback_search(collection, query: str, *, top_k: int) -> List[Dict[str, Any]]:
    terms = _build_fallback_terms(query)
    if not terms:
        # Last resort: use the first N chars of query
        pattern = re.escape((query or "").strip()[:64])
        if not pattern:
            return []
        terms = [pattern]

    pattern = "(" + "|".join(re.escape(t) for t in terms) + ")"
    docs = list(collection.find({"content_text": {"$regex": pattern, "$options": "i"}}).limit(top_k * 5))
    if not docs:
        return []

    lower_terms = [t.lower() for t in terms]
    for d in docs:
        text = str(d.get("content_text") or "").lower()
        d["_fallback_score"] = sum(text.count(t) for t in lower_terms)
    docs.sort(key=lambda x: x.get("_fallback_score", 0), reverse=True)
    for d in docs:
        d.pop("_fallback_score", None)
    return docs[:top_k]


def _contains_any_phrase(text: str, phrases: List[str]) -> bool:
    t = (text or "").lower()
    return any(p.lower() in t for p in phrases)

def search_knowledge(
    query: str,
    limit: int | None = None,
    num_candidates: int | None = None,
    use_hybrid: bool = True,
) -> List[Dict[str, Any]]:

    top_k = limit or VECTOR_TOP_K
    candidates = num_candidates or VECTOR_NUM_CANDIDATES

    if use_hybrid:
        logger.info("Gemini retriever: use_hybrid=True ignored (dense-only).")

    collection = get_collection(MONGO_VECTOR_COLLECTION_GEMINI)
    return _search_dense_only(query, top_k, candidates, collection)


def _search_dense_only(
    query: str, 
    top_k: int, 
    candidates: int, 
    collection
) -> List[Dict[str, Any]]:
    query_vector = _get_embedder().embed_query(query)
    
    project_stage = {
        "content_text": 1,
        "chapter": 1,
        "topic": 1,
        "page_id": 1,
        "page_ids": 1,
        "source": 1,
        "score": {"$meta": "vectorSearchScore"},
    }
    
    try:
        results = aggregate_vector_search_with_optional_filter(
            collection=collection,
            query_vector=query_vector,
            candidates=candidates,
            limit=top_k,
            project_stage=project_stage,
            embedding_model_filter=MODEL_EMBEDDING,
        )
        logger.info(f"Dense search returned {len(results)} results")
    except Exception as e:
        logger.warning("Vector search failed, fallback to text search. Error: %s", e)
        results = []

    phrase_terms = _build_fallback_terms(query)
    if results and phrase_terms:
        filtered = [r for r in results if _contains_any_phrase(str(r.get("content_text") or ""), phrase_terms)]
        if filtered:
            logger.info("Vector results filtered by phrases=%s -> %s/%s kept", phrase_terms, len(filtered), len(results))
            results = filtered
        else:
            logger.warning(
                "Vector results contain none of phrases=%s. Falling back to phrase-regex for better relevance.",
                phrase_terms,
            )
            results = _regex_fallback_search(collection, query, top_k=top_k)
    
    # Optional score filter
    if VECTOR_SCORE_THRESHOLD is not None and results:
        results = [r for r in results if r.get("score", 0) >= VECTOR_SCORE_THRESHOLD]

    # Fallback text search if no results
    if not results:
        logger.info("No vector results, trying text/regex fallback")
        try:
            phrase_terms = _build_fallback_terms(query)
            if phrase_terms:
                logger.info("Using phrase-regex fallback terms=%s", phrase_terms)
                results = _regex_fallback_search(collection, query, top_k=top_k)

            if not results:
                results = list(collection.find({"$text": {"$search": query}}).limit(top_k))

            if not results:
                logger.info("Text search returned 0 results, falling back to regex search")
                results = _regex_fallback_search(collection, query, top_k=top_k)
        except Exception as text_err:
            logger.warning(f"Text search also failed: {text_err}")
            logger.info("Using regex fallback search")
            results = _regex_fallback_search(collection, query, top_k=top_k)
        
    return results