import os
import fitz
import json
import time
import re
import signal
import sys
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv
from google.genai import types
from app.services.key_manager_gemini import GeminiKeyManager
from app.utils.prompts import HISTORY_PAGE_EXTRACTION_PROMPT_NEW
from app.utils.config import (
    MAX_PAGES_PER_PDF,
    RATE_LIMIT_DELAY,
    PDF_ZOOM_MATRIX,
    DATA_DIR,
    OUTPUT_JSON_DATA,
    ENV_FILE,
    MODEL_EXTRACT,
    EXTRACT_GENERATION_CONFIG,
    MONGO_COLLECTION_NAME_TEST,
    SAVE_BATCH_SIZE,
)
from app.databases.database import get_collection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv(ENV_FILE)

extract_key_manager = GeminiKeyManager(
    model_name=MODEL_EXTRACT,
    generation_config=EXTRACT_GENERATION_CONFIG
)

# Global variables để handle graceful shutdown
_pending_save = {"local_db": None, "pages_since_save": 0}


def _signal_handler(signum, frame):
    """Handle signal to save data before exiting."""
    if _pending_save["local_db"] and _pending_save["pages_since_save"] > 0:
        logger.info("\n⚠️  Interrupted! Saving pending data...")
        save_local_db(_pending_save["local_db"])
        logger.info(f"✅ Saved {_pending_save['pages_since_save']} pending pages")
    sys.exit(0)

def _recover_context(pdf_name: str, existing_records: Dict[str, Any]) -> Tuple[str, str]:
    """Recover context from the last processed page in the PDF."""
    pdf_pages = [k for k in existing_records.keys() if k.startswith(f"{pdf_name}_p")]
    if not pdf_pages:
        return "Undetermined", "Undetermined"
    
    try:
        last_page_id = sorted(pdf_pages, key=lambda x: int(x.rsplit("_p", 1)[1]))[-1]
        page_info = existing_records[last_page_id].get("data", {}).get("page_info", {})
        chapter = page_info.get("chapter", "Undetermined")
        topic = page_info.get("topic", "Undetermined")
        logger.info(f"📌 Resume context: {topic}")
        return chapter, topic
    except (ValueError, IndexError):
        logger.warning("⚠️  Không thể parse page number, dùng context mặc định")
    
    return "Undetermined", "Undetermined"

def _get_context_from_record(record: Dict[str, Any]) -> Tuple[str, str]:
    """Extract context từ existing record."""
    page_info = record.get("data", {}).get("page_info", {})
    return page_info.get("chapter", "Undetermined"), page_info.get("topic", "Undetermined")

def _save_record(record: Dict[str, Any], unique_id: str, page_num: int, local_db: list, existing_records: Dict[str, Any]) -> None:
    """Save record to MongoDB and local_db."""
    try:
        get_collection(MONGO_COLLECTION_NAME_TEST).update_one(
            {"doc_id": unique_id}, {"$set": record}, upsert=True
        )
    except Exception as e:
        logger.error(f"  ❌ Error saving to MongoDB (page {page_num}): {e}")
    
    local_db.append(record)
    existing_records[unique_id] = record

def _process_page(
    doc, i: int, pdf_name: str, total_pages: int,
    current_chapter: str, current_topic: str,
    existing_records: Dict[str, Any], local_db: list
) -> Tuple[str, str, int]:
    """Process a page and return updated context + pages_since_save."""
    page_num = i + 1
    unique_id = f"{pdf_name}_p{page_num}"
    
        # Early return nếu đã tồn tại
    if existing_record := existing_records.get(unique_id):
        current_chapter, current_topic = _get_context_from_record(existing_record)
        logger.info(f"  ⏭️  Page {page_num}/{total_pages}: Đã tồn tại. Context: {current_topic}")
        return current_chapter, current_topic, 0
    
    logger.info(f"  🔄 Page {page_num}/{total_pages}: Đang extract với context: {current_topic}")
    
    # Extract
    page = doc.load_page(i)
    pix = page.get_pixmap(matrix=fitz.Matrix(PDF_ZOOM_MATRIX, PDF_ZOOM_MATRIX))
    ai_data = get_ultimate_ai_data(pix.tobytes("png"), page_num, pdf_name, current_chapter, current_topic)
    
    # Early return nếu extract/validate fail
    if not ai_data or not validate_extracted_data(ai_data, page_num):
        logger.warning(f"  ⚠️  Page {page_num}: Invalid data or extraction failed")
        return current_chapter, current_topic, 0
    
    # Update context và save
    current_chapter = ai_data["page_info"]["chapter"]
    current_topic = ai_data["page_info"]["topic"]
    
    record = {
        "doc_id": unique_id,
        "source": pdf_name,
        "page_id": page_num,
        "data": ai_data,
        "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    _save_record(record, unique_id, page_num, local_db, existing_records)
    logger.info(f"  ✅ Page {page_num}/{total_pages}: Đã lưu ({current_topic})")
    
    return current_chapter, current_topic, 1

def process_ultimate_pipeline() -> None:
    """Pipeline to extract data from PDF to MongoDB and local JSON with new structure."""
    local_db = load_local_db()
    
    # Early returns với guard clauses
    if not os.path.exists(DATA_DIR):
        return logger.warning(f"❌ DATA_DIR not found: {DATA_DIR}")

    pdf_files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith(".pdf")])
    if not pdf_files:
        return logger.warning(f"❌ No PDF files found in {DATA_DIR}")
    
    logger.info(f"📚 Found {len(pdf_files)} PDF files: {', '.join(pdf_files)}")
    existing_records = {item.get("doc_id"): item for item in local_db if item.get("doc_id")}
    logger.info(f"📊 Đã có {len(existing_records)} pages trong database")

    for pdf_name in pdf_files:
        logger.info(f"\n{'='*60}\n📄 Processing: {pdf_name}\n{'='*60}")
        pdf_path = os.path.join(DATA_DIR, pdf_name)
        current_chapter, current_topic = _recover_context(pdf_name, existing_records)

        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc) if MAX_PAGES_PER_PDF == -1 else min(len(doc), MAX_PAGES_PER_PDF)
            pages_to_process = sum(1 for i in range(total_pages) if f"{pdf_name}_p{i + 1}" not in existing_records)
            logger.info(f"📖 Tổng: {total_pages} | Cần: {pages_to_process} | Đã có: {total_pages - pages_to_process}")

            pages_since_save = 0
            _pending_save["local_db"] = local_db
            _pending_save["pages_since_save"] = 0
            
            try:
                for i in range(total_pages):
                    current_chapter, current_topic, saved = _process_page(
                        doc, i, pdf_name, total_pages, current_chapter, current_topic,
                        existing_records, local_db
                    )
                    pages_since_save += saved
                    _pending_save["pages_since_save"] = pages_since_save
                    
                    if pages_since_save >= SAVE_BATCH_SIZE:
                        save_local_db(local_db)
                        pages_since_save = _pending_save["pages_since_save"] = 0
                        logger.debug(f"  💾 Batch saved ({SAVE_BATCH_SIZE} pages)")
                    
                    time.sleep(RATE_LIMIT_DELAY)
            finally:
                # Đảm bảo save khi có exception hoặc dừng giữa chừng
                if pages_since_save > 0:
                    save_local_db(local_db)
                    logger.info(f"  💾 Final save ({pages_since_save} pages)")
                    _pending_save["pages_since_save"] = 0
            
            doc.close()
            logger.info(f"✅ Finished processing {pdf_name}")
        except Exception as e:
            logger.error(f"❌ Error processing {pdf_name}: {e}", exc_info=True)

    logger.info(f"\n{'='*60}")
    logger.info("✅ Pipeline Finished!")
    logger.info(f"{'='*60}")

def validate_extracted_data(data: Dict[str, Any], page_num: int) -> bool:
    """Validate schema: page_info + content_segments."""
    if not isinstance(data, dict):
        logger.error(f"  ❌ Page {page_num}: data is not a dict")
        return logger.error(f"  ❌ Page {page_num}: data is not a dict") or False
    
    page_info = data.get("page_info")
    if not isinstance(page_info, dict):
        logger.error(f"  ❌ Page {page_num}: thiếu hoặc không hợp lệ 'page_info'")
        return logger.error(f"  ❌ Page {page_num}: thiếu hoặc không hợp lệ 'page_info'") or False
    
    required = ["page_id", "type", "chapter", "topic"]
    if missing := [f for f in required if f not in page_info]:
        logger.error(f"  ❌ Page {page_num}: page_info thiếu fields: {missing}")
        return logger.error(f"  ❌ Page {page_num}: page_info thiếu fields: {missing}") or False
    
    if not isinstance(data.get("content_segments", []), list):
        logger.error(f"  ❌ Page {page_num}: 'content_segments' không phải list")
        return logger.error(f"  ❌ Page {page_num}: 'content_segments' không phải list") or False
    
    if page_info.get("page_id") != page_num:
        logger.warning(f"  ⚠️  Page {page_num}: page_id không khớp ({page_info.get('page_id')} vs {page_num})")
    
    return True

def get_ultimate_ai_data(image_bytes: bytes, page_num: int, filename: str, last_chapter: str, last_topic: str) -> Optional[Dict[str, Any]]:
    """Extract data from PDF page image using Gemini Vision API."""
    if not extract_key_manager:
        logger.error(f"  ❌ Page {page_num}: Extract key_manager không được khởi tạo")
        return None
    
    try:
        prompt = HISTORY_PAGE_EXTRACTION_PROMPT_NEW.format(
            page_num=page_num, filename=filename, last_chapter=last_chapter, last_topic=last_topic
        )
        image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")
        response = extract_key_manager.generate_content([prompt, image_part])
        
        if not hasattr(response, 'text') or not response.text:
            logger.error(f"  ❌ Page {page_num}: Response không có text")
            return None
        
        if len(response.text) < 100:
            logger.warning(f"  ⚠️  Page {page_num}: Response quá ngắn ({len(response.text)} chars)")
        
        try:
            return _parse_response_text(response.text)
        except json.JSONDecodeError as json_err:
            logger.error(f"  ❌ Page {page_num}: JSON decode error: {json_err}\n     Response (first 500): {response.text[:500]}")
            return None
    except Exception as e:
        logger.error(f"  ❌ Page {page_num}: Exception: {e}", exc_info=True)
        return None

def _parse_response_text(text: str) -> Dict[str, Any]:
    """Parse JSON from response text with fallback strategies."""
    original = text.strip()
    candidates = [original]
    
    # Fix trailing commas
    no_trailing_commas = re.sub(r",\s*([}\]])", r"\1", original)
    candidates.append(no_trailing_commas)
    
    # Balance brackets
    def _balance_brackets(s: str) -> str:
        s += "}" * (s.count("{") - s.count("}"))
        s += "]" * (s.count("[") - s.count("]"))
        return s
    
    candidates.append(_balance_brackets(no_trailing_commas))
    
    # Try last complete object
    last_curly = no_trailing_commas.rfind("}")
    if last_curly != -1:
        candidates.append(_balance_brackets(no_trailing_commas[:last_curly + 1]))
    
    # Fix quotes
    for c in list(candidates):
        if c.count('"') % 2 != 0:
            candidates.append(c + '"')
    
    # Try parsing
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    
    raise json.JSONDecodeError("Unrecoverable JSON", original, 0)

def load_local_db() -> list:
    """Load local database from file test_structure_data_new.json."""
    if not os.path.exists(OUTPUT_JSON_DATA) or os.path.getsize(OUTPUT_JSON_DATA) == 0:
        return []

    try:
        with open(OUTPUT_JSON_DATA, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        backup_path = f"{OUTPUT_JSON_DATA}.bak"
        try:
            os.replace(OUTPUT_JSON_DATA, backup_path)
            logger.warning(f"Local DB corrupted, backed up to {backup_path}. Error: {e}")
        except OSError:
            logger.warning(f"Local DB corrupted and cannot be moved. Error: {e}")
    except IOError as e:
        logger.warning(f"Failed to load local DB: {e}")
    
    return []

def save_local_db(local_db: list) -> None:
    """Save local database vào file test_structure_data_new.json."""
    with open(OUTPUT_JSON_DATA, "w", encoding="utf-8") as f:
        json.dump(local_db, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
    process_ultimate_pipeline()