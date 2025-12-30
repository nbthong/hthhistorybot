import os

# ============================================================================
# Path Configuration
# ============================================================================
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

# Output JSON file path
OUTPUT_JSON = os.path.join(EXTRACT_DATA_DIR, "history_ultimate_db.json")


# ============================================================================
# AI Configuration
# ============================================================================

# model name
PREFERRED_MODEL = "gemini-2.5-flash"

# Generation configuration
GENERATION_CONFIG = {
    "temperature": 0.5,
    "response_mime_type": "application/json",
}


# ============================================================================
# PDF Processing Configuration
# ============================================================================

# Maximum number of pages to process per PDF file
MAX_PAGES_PER_PDF = -1

# Delay between API calls to respect rate limits
RATE_LIMIT_DELAY = 2  # seconds

# Delay when retrying after rate limit error
RATE_LIMIT_RETRY_DELAY = 10  # seconds

# Zoom matrix for PDF page rendering
PDF_ZOOM_MATRIX = 2.5


# ============================================================================
# MongoDB Configuration
# ============================================================================

MONGO_DB_NAME = "history_tutor_db"
MONGO_COLLECTION_NAME = "knowledge_base"
MONGO_VECTOR_COLLECTION = "knowledge_vectors"


CHROMA_PERSIST_DIR = os.path.join(PROJECT_ROOT, "chroma_db")


# Chunking configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100

# Model Embedding Local
GEMINI_EMBEDDING_MODEL = "models/text-embedding-004"
LOCAL_EMBEDDING_MODEL = "all-MiniLM-L6-v2"