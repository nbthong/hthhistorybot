import logging
from app.databases.database import ensure_kb_indexes, get_database, ensure_chat_history_indexes
from app.databases.vector_store import ensure_vector_indexes
from app.utils.config import MONGO_COLLECTION_NAME, MONGO_VECTOR_COLLECTION_GEMINI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_indexes():
    db = get_database()
    
    # Collection knowledge_base
    logger.info(f"Setting up indexes for '{MONGO_COLLECTION_NAME}'...")
    ensure_kb_indexes()
    logger.info("✅ KB indexes ensured")
    
    # Collection knowledge_vectors
    logger.info(f"\nSetting up indexes for '{MONGO_VECTOR_COLLECTION_GEMINI}'...")
    ensure_vector_indexes(MONGO_VECTOR_COLLECTION_GEMINI)
    logger.info("✅ Vector indexes ensured")
    
    # Collection chat_history
    logger.info("\nSetting up indexes for 'chat_history'...")
    ensure_chat_history_indexes()
    logger.info("✅ Chat history indexes ensured")
    
    # Vector Search Index (only MongoDB Atlas supported)
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
    
    for coll_name in [MONGO_COLLECTION_NAME, MONGO_VECTOR_COLLECTION_GEMINI]:
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

