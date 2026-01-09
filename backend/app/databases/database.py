import os
import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from dotenv import load_dotenv
from app.utils.config import (
    ENV_FILE,
    MONGO_COLLECTION_NAME,
    MONGO_DB_NAME,
    MONGO_CHAT_HISTORY_COLLECTION,
)
from datetime import datetime


logger = logging.getLogger(__name__)

load_dotenv(ENV_FILE)

_client: Optional[MongoClient] = None
_db: Optional[Database] = None
_collection: Optional[Collection] = None


def get_mongo_uri() -> str:
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise ValueError("MONGO_URI environment variable is not set!")
    return mongo_uri


def connect() -> MongoClient:
    global _client, _db, _collection

    if _client is not None:
        return _client

    mongo_uri = get_mongo_uri()

    try:
        _client = MongoClient(mongo_uri)
        _client.admin.command("ping")
        _db = _client[MONGO_DB_NAME]
        _collection = _db[MONGO_COLLECTION_NAME]
        logger.info(
            f"Connected to MongoDB (DB: {MONGO_DB_NAME}, Collection: {MONGO_COLLECTION_NAME})"
        )
        return _client
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


def get_client() -> MongoClient:
    if _client is None:
        connect()
    return _client


def get_database() -> Database:
    if _db is None:
        connect()
    return _db


def get_collection(name: str | None = None) -> Collection:
    if _client is None or _db is None or _collection is None:
        connect()

    if name:
        return _db[name]
    return _collection


def get_kb_collection() -> Collection:
    return get_collection(MONGO_COLLECTION_NAME)


def ensure_kb_indexes() -> None:
    kb = get_kb_collection()
    try:
        kb.create_index("doc_id", unique=True)
    except Exception as e:
        logger.warning("KB index 'doc_id' may already exist: %s", e)
    try:
        kb.create_index("page_id")
    except Exception as e:
        logger.warning("KB index 'page_id' may already exist: %s", e)


def close_connection() -> None:
    global _client, _db, _collection

    if _client is not None:
        _client.close()
        _client = None
        _db = None
        _collection = None
        logger.info("MongoDB connection closed.")


def health_check() -> bool:
    try:
        if _client is None:
            return False
        _client.admin.command("ping")
        return True
    except Exception as e:
        logger.warning(f"MongoDB health check failed: {e}")
        return False


try:
    connect()
except Exception as e:
    logger.warning(f"Failed to initialize MongoDB connection: {e}")
    logger.warning("MongoDB operations will fail until connection is established.")

def get_history_from_mongo(user_id: str, session_id: Optional[str] = None, limit: int = 50):
    col = get_collection(MONGO_CHAT_HISTORY_COLLECTION)
    query = {"user_id": user_id}
    if session_id:
        query["session_id"] = session_id
    
    cursor = col.find(query).sort("timestamp", 1).limit(limit) 
    return list(cursor)

def save_message_to_mongo(user_id: str, session_id: str, role: str, content: str):
    col = get_collection(MONGO_CHAT_HISTORY_COLLECTION)
    col.insert_one({
        "user_id": user_id,
        "session_id": session_id,
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow()
    })