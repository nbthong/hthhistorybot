import logging
from app.databases.database import get_database, get_collection
from app.utils.config import MONGO_VECTOR_COLLECTION, MONGO_COLLECTION_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_indexes():
    db = get_database()
    
    # Collection knowledge_base
    logger.info(f"Setting up indexes for '{MONGO_COLLECTION_NAME}'...")
    kb_collection = db[MONGO_COLLECTION_NAME]
    
    try:
        # Unique index trên doc_id
        kb_collection.create_index("doc_id", unique=True)
        logger.info("✅ Created unique index on 'doc_id'")
    except Exception as e:
        logger.warning(f"Index 'doc_id' may already exist: {e}")
    
    try:
        # Index trên page_id để query nhanh
        kb_collection.create_index("page_id")
        logger.info("✅ Created index on 'page_id'")
    except Exception as e:
        logger.warning(f"Index 'page_id' may already exist: {e}")
    
    # Collection knowledge_vectors
    logger.info(f"\nSetting up indexes for '{MONGO_VECTOR_COLLECTION}'...")
    vector_collection = db[MONGO_VECTOR_COLLECTION]
    
    try:
        # Compound unique index: (doc_id, content_text)
        vector_collection.create_index(
            [("doc_id", 1), ("content_text", 1)],
            unique=True
        )
        logger.info("✅ Created compound unique index on ('doc_id', 'content_text')")
    except Exception as e:
        logger.warning(f"Compound index may already exist: {e}")
    
    try:
        # Index trên embedding_model (quan trọng cho vector search filter)
        vector_collection.create_index("embedding_model")
        logger.info("✅ Created index on 'embedding_model'")
    except Exception as e:
        logger.warning(f"Index 'embedding_model' may already exist: {e}")
    
    try:
        # Text index trên content_text cho $text search
        vector_collection.create_index([("content_text", "text")])
        logger.info("✅ Created text index on 'content_text'")
    except Exception as e:
        logger.warning(f"Text index may already exist: {e}")
    
    try:
        # Index trên page_id
        vector_collection.create_index("page_id")
        logger.info("✅ Created index on 'page_id'")
    except Exception as e:
        logger.warning(f"Index 'page_id' may already exist: {e}")
    
    # 3. Vector Search Index (chỉ MongoDB Atlas hỗ trợ)
    logger.info("\n" + "="*60)
    logger.info("⚠️  VECTOR SEARCH INDEX (Chỉ trên MongoDB Atlas)")
    logger.info("="*60)
    logger.info("✅ Index setup completed!")
    logger.info("="*60)


def list_indexes():
    db = get_database()
    
    logger.info("\n" + "="*60)
    logger.info("CURRENT INDEXES")
    logger.info("="*60)
    
    for coll_name in [MONGO_COLLECTION_NAME, MONGO_VECTOR_COLLECTION]:
        logger.info(f"\nCollection: {coll_name}")
        collection = db[coll_name]
        indexes = list(collection.list_indexes())
        for idx in indexes:
            logger.info(f"  - {idx['name']}: {idx.get('key', {})}")


if __name__ == "__main__":
    logger.info("🚀 MongoDB Index Setup Script")
    logger.info("="*60)
    
    try:
        create_indexes()
        list_indexes()
    except Exception as e:
        logger.error(f"❌ Error during index setup: {e}", exc_info=True)
        logger.info("\n💡 If error about permissions, run with admin MongoDB account")

