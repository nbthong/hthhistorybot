from app.databases.database import get_collection
from app.chunk_embedding.embedder import HybridEmbedder
from app.utils.config import MONGO_VECTOR_COLLECTION

embedder = HybridEmbedder()

def search_knowledge(query: str, limit: int = 5):
    query_vector = embedder.embed_query(query)
    collection = get_collection(MONGO_VECTOR_COLLECTION)
    
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding_vector",
                "queryVector": query_vector,
                "numCandidates": 100,
                "limit": limit
            }
        },
        {
            "$project": {
                "content_text": 1,
                "chapter": 1,
                "topic": 1,
                "page_id": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]
    
    results = list(collection.aggregate(pipeline))
    
    if not results:
        results = list(collection.find({"$text": {"$search": query}}).limit(limit))
        
    return results