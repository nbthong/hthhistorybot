from app.databases.database import get_collection
from app.databases.vector_store import aggregate_vector_search_with_optional_filter
from app.chunk_embedding.embedder import HybridEmbedder
from app.utils.config import (
    LOCAL_EMBEDDING_MODEL,
    MONGO_VECTOR_COLLECTION,
    MONGO_VECTOR_COLLECTION_NEW,
    VECTOR_TOP_K,
    VECTOR_NUM_CANDIDATES,
    VECTOR_SCORE_THRESHOLD,
    USE_SPARSE_EMBEDDING,
    HYBRID_SEARCH_DENSE_WEIGHT,
    HYBRID_SEARCH_SPARSE_WEIGHT,
)
from typing import List, Dict, Any

import logging

logger = logging.getLogger(__name__)

embedder = HybridEmbedder(use_sparse=USE_SPARSE_EMBEDDING, use_colbert=False)

def search_knowledge(
    query: str,
    limit: int | None = None,
    num_candidates: int | None = None,
    use_hybrid: bool = True,
) -> List[Dict[str, Any]]:

    top_k = limit or VECTOR_TOP_K
    candidates = num_candidates or VECTOR_NUM_CANDIDATES
    # collection = get_collection(MONGO_VECTOR_COLLECTION_NEW)
    collection = get_collection(MONGO_VECTOR_COLLECTION)
    
    # If sparse is not enabled or hybrid is not desired, use dense only
    if not USE_SPARSE_EMBEDDING or not use_hybrid:
        return _search_dense_only(query, top_k, candidates, collection)
    
    # Hybrid search: dense + sparse
    return _search_hybrid(query, top_k, candidates, collection)


def _search_dense_only(
    query: str, 
    top_k: int, 
    candidates: int, 
    collection
) -> List[Dict[str, Any]]:
    query_vector = embedder.embed_query(query)
    
    project_stage = {
        "content_text": 1,
        "chapter": 1,
        "topic": 1,
        "page_id": 1,
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
            embedding_model_filter=LOCAL_EMBEDDING_MODEL,
        )
        logger.info(f"Dense search returned {len(results)} results")
    except Exception as e:
        logger.warning("Vector search failed, fallback to text search. Error: %s", e)
        results = []
    
    # Optional score filter
    if VECTOR_SCORE_THRESHOLD is not None and results:
        results = [r for r in results if r.get("score", 0) >= VECTOR_SCORE_THRESHOLD]

    # Fallback text search if no results
    if not results:
        logger.info("No vector results, trying text search fallback")
        try:
            results = list(collection.find({"$text": {"$search": query}}).limit(top_k))
        except Exception as text_err:
            logger.warning(f"Text search also failed: {text_err}")
            # Fallback last: simple regex search (slow but still returns results)
            logger.info("Using regex fallback search")
            results = list(
                collection.find(
                    {"content_text": {"$regex": query, "$options": "i"}}
                ).limit(top_k)
            )
        
    return results


def _search_hybrid(
    query: str,
    top_k: int,
    candidates: int,
    collection
) -> List[Dict[str, Any]]:
    # Embed query with both dense + sparse
    query_output = embedder.embed_documents(
        [query],
        return_dense=True,
        return_sparse=True,
        return_colbert=False
    )
    
    if isinstance(query_output, dict):
        query_vector = query_output["dense_vecs"][0]
        query_lexical = query_output.get("lexical_weights", [None])[0]
    else:
        query_vector = query_output[0]
        query_lexical = None
    
    # Get more candidates to have enough for re-ranking
    retrieval_limit = min(top_k * 3, candidates)
    
    project_stage = {
        "content_text": 1,
        "chapter": 1,
        "topic": 1,
        "page_id": 1,
        "source": 1,
        "lexical_weights": 1,  # Get sparse weights of document
        "dense_score": {"$meta": "vectorSearchScore"},
    }
    
    try:
        candidates_results = aggregate_vector_search_with_optional_filter(
            collection=collection,
            query_vector=query_vector,
            candidates=candidates,
            limit=retrieval_limit,
            project_stage=project_stage,
            embedding_model_filter=LOCAL_EMBEDDING_MODEL,
        )
        logger.info(f"Dense search returned {len(candidates_results)} candidates for hybrid re-ranking")
    except Exception as e:
        logger.warning("Hybrid search failed, fallback to dense only. Error: %s", e)
        return _search_dense_only(query, top_k, candidates, collection)
    
    if not candidates_results:
        logger.info("No candidates, trying text search fallback")
        try:
            return list(collection.find({"$text": {"$search": query}}).limit(top_k))
        except Exception as text_err:
            logger.warning(f"Text search failed: {text_err}")
            # Fallback regex
            logger.info("Using regex fallback search")
            return list(
                collection.find(
                    {"content_text": {"$regex": query, "$options": "i"}}
                ).limit(top_k)
            )
    
    # Re-rank với hybrid score
    if query_lexical:
        for doc in candidates_results:
            dense_score = doc.get("dense_score", 0.0)
            
            # Compute lexical score if document has lexical_weights
            lexical_score = 0.0
            doc_lexical = doc.get("lexical_weights")
            if doc_lexical:
                try:
                    lexical_score = embedder.compute_lexical_score(query_lexical, doc_lexical)
                except Exception as e:
                    logger.debug(f"Failed to compute lexical score: {e}")
            
            # Hybrid score
            hybrid_score = (
                HYBRID_SEARCH_DENSE_WEIGHT * dense_score +
                HYBRID_SEARCH_SPARSE_WEIGHT * lexical_score
            )
            doc["score"] = hybrid_score
            doc["dense_score_raw"] = dense_score
            doc["lexical_score"] = lexical_score
    else:
        # If no query lexical, use dense score
        for doc in candidates_results:
            doc["score"] = doc.get("dense_score", 0.0)
    
    # Sort by hybrid score
    candidates_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    # Filter by threshold if exists
    if VECTOR_SCORE_THRESHOLD is not None:
        candidates_results = [r for r in candidates_results if r.get("score", 0) >= VECTOR_SCORE_THRESHOLD]
    
    # Return top_k
    results = candidates_results[:top_k]
    
    logger.info(
        f"Hybrid search: returned {len(results)} results "
        f"(dense_weight={HYBRID_SEARCH_DENSE_WEIGHT}, sparse_weight={HYBRID_SEARCH_SPARSE_WEIGHT})"
    )
    
    return results