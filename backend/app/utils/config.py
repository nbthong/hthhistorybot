import os
from google.genai import types

# Path Configuration
def get_project_root() -> str:
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.dirname(current_file_dir) 
    project_root = os.path.dirname(app_dir) 
    return project_root


# Project root directory (calculated once)
PROJECT_ROOT = get_project_root()

# Environment file path
ENV_FILE = os.path.join(PROJECT_ROOT, ".env")

# Directory containing raw textbook PDFs (moved from 'data' -> 'resources')
DATA_DIR = os.path.join(PROJECT_ROOT, "app", "resources")

# Extract data directory (where history_ultimate_db.json is stored)
EXTRACT_DATA_DIR = os.path.join(PROJECT_ROOT, "app", "extract_data")

# Output JSON file path extract data
OUTPUT_JSON_DATA = os.path.join(EXTRACT_DATA_DIR, "history_ultimate_db.json")

# Output JSON file path chunk embedding
OUTPUT_JSON_CHUNK_EMBEDDING_GEMINI = os.path.join(EXTRACT_DATA_DIR, "merge_content_gemini.json")

# model name
MODEL_EXTRACT = "gemini-2.5-flash" 
MODEL_GEN_IMAGE = "gemini-2.5-flash-image"
MODEL_EMBEDDING = "text-embedding-004"
MODEL_ANSWER = "gemini-2.0-flash"  
PREFERRED_MODEL = MODEL_ANSWER 

# Maximum number of pages to process per PDF file
MAX_PAGES_PER_PDF = -1

# Delay between API calls to respect rate limits
RATE_LIMIT_DELAY = 2  # seconds

# Delay when retrying after rate limit error
RATE_LIMIT_RETRY_DELAY = 10  # seconds

# Zoom matrix for PDF page rendering
PDF_ZOOM_MATRIX = 2.5

# Batch save configuration (save every N pages to reduce I/O)
SAVE_BATCH_SIZE = 10  # Save to file every N pages

# Generation configuration for streaming (plain text response)
TEXT_GENERATION_CONFIG_STREAM = types.GenerateContentConfig(
    temperature=0.5,
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
)

TEXT_GENERATION_CONFIG = types.GenerateContentConfig(
    temperature=0.5,
    response_mime_type="application/json",
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
)

GENERATION_CONFIG = {
    "temperature": 0.5,
    "response_mime_type": "application/json",
    "automatic_function_calling": types.AutomaticFunctionCallingConfig(disable=True)
}

# Generation config for extract
EXTRACT_GENERATION_CONFIG = {
    "temperature": 0.1,  
    "response_mime_type": "application/json",
    "max_output_tokens": 8192,  
    "automatic_function_calling": types.AutomaticFunctionCallingConfig(disable=True)
}

# Vector search defaults
VECTOR_TOP_K = 5
VECTOR_NUM_CANDIDATES = 50
VECTOR_SCORE_THRESHOLD: float | None = None
USE_EMBEDDING_MODEL_FILTER = True 

# MongoDB Configuration
MONGO_DB_NAME = "history_tutor_db"
MONGO_COLLECTION_NAME = "knowledge_base"
MONGO_HISTORY_COLLECTION = "chat_history"
MONGO_VECTOR_COLLECTION_GEMINI = "knowledge_vectors_gemini"

MONGO_ATLAS_VECTOR_INDEX_NAME = "vector_index"
MONGO_ATLAS_VECTOR_PATH = "embedding_vector"

# Chunking configuration
CHUNK_SIZE = 1024
CHUNK_OVERLAP = 200
EMBED_BATCH_SIZE = 96
MONGO_BULK_WRITE_BATCH_SIZE = 500

# Embedding mode configuration
USE_SPARSE_EMBEDDING = True  # Enable sparse vectors (lexical matching, BM25-like)
USE_COLBERT_EMBEDDING = False  # Disable ColBERT (RAM intensive, slower)

# Hybrid search weights
HYBRID_SEARCH_DENSE_WEIGHT = 0.7  # Weight for dense vector search (0-1)
HYBRID_SEARCH_SPARSE_WEIGHT = 0.3  # Weight for sparse/lexical search (0-1)

LIMIT_WORD_COUNT_GENERATE_IMAGE = 70