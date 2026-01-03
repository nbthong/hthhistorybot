import os
import fitz
import json
import time
import re
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from google.genai import types
from app.services.key_manager_gemini import GeminiKeyManager, API_KEYS
from app.utils.prompts import HISTORY_PAGE_EXTRACTION_PROMPT
from app.utils.config import (
    MAX_PAGES_PER_PDF,
    RATE_LIMIT_DELAY,
    RATE_LIMIT_RETRY_DELAY,
    PDF_ZOOM_MATRIX,
    DATA_DIR,
    OUTPUT_JSON,
    ENV_FILE,
    MODEL_EXTRACT,
    EXTRACT_GENERATION_CONFIG,
)
from app.databases.database import get_collection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv(ENV_FILE)

if API_KEYS:
    extract_key_manager = GeminiKeyManager(
        API_KEYS,
        model_id=MODEL_EXTRACT,
        generation_config=EXTRACT_GENERATION_CONFIG
    )
    logger.info(f"✅ Extract key_manager initialized with model: {MODEL_EXTRACT}")
else:
    extract_key_manager = None
    logger.error("❌ No API keys found! Extract pipeline will fail.")


def process_ultimate_pipeline() -> None:
    """Pipeline to extract data from PDF to MongoDB and local JSON."""
    if not extract_key_manager:
        logger.error("❌ Extract key_manager not initialized. Please check API keys.")
        return
    
    local_db = load_local_db()
    if not os.path.exists(DATA_DIR):
        logger.warning(f"❌ DATA_DIR not found: {DATA_DIR}")
        return

    pdf_files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith(".pdf")])
    if not pdf_files:
        logger.warning(f"❌ No PDF files found in {DATA_DIR}")
        return
    
    logger.info(f"📚 Found {len(pdf_files)} PDF files: {', '.join(pdf_files)}")

    for pdf_name in pdf_files:
        logger.info(f"\n{'='*60}")
        logger.info(f"📄 Processing: {pdf_name}")
        logger.info(f"{'='*60}")
        pdf_path = os.path.join(DATA_DIR, pdf_name)

        # Initialize context for each new PDF file
        current_chapter = "Undetermined"
        current_topic = "Undetermined"

        try:
            doc = fitz.open(pdf_path)
            total_pages = (
                len(doc)
                if MAX_PAGES_PER_PDF == -1
                else min(len(doc), MAX_PAGES_PER_PDF)
            )
            logger.info(f"📖 Tổng số trang: {total_pages}")

            for i in range(total_pages):
                page_num = i + 1
                unique_id = f"{pdf_name}_p{page_num}"

                existing_record = next(
                    (item for item in local_db if item.get("doc_id") == unique_id), None
                )
                if existing_record:
                    current_chapter = existing_record["data"]["page_info"]["chapter"]
                    current_topic = existing_record["data"]["page_info"]["topic"]
                    logger.info(
                        f"  ⏭️  Page {page_num}/{total_pages}: Đã tồn tại. Context: {current_topic}"
                    )
                    continue

                logger.info(
                    f"  🔄 Page {page_num}/{total_pages}: Đang extract với context: {current_topic}"
                )

                page = doc.load_page(i)
                pix = page.get_pixmap(
                    matrix=fitz.Matrix(PDF_ZOOM_MATRIX, PDF_ZOOM_MATRIX)
                )

                ai_data = get_ultimate_ai_data(
                    pix.tobytes("png"),
                    page_num,
                    pdf_name,
                    current_chapter,
                    current_topic,
                )

                if ai_data and validate_extracted_data(ai_data, page_num):
                    current_chapter = ai_data["page_info"]["chapter"]
                    current_topic = ai_data["page_info"]["topic"]

                    record = {
                        "doc_id": unique_id,
                        "source": pdf_name,
                        "page_id": page_num,
                        "data": ai_data,
                        "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    }

                    # Save to MongoDB
                    try:
                        get_collection().update_one(
                            {"doc_id": unique_id}, {"$set": record}, upsert=True
                        )
                    except Exception as e:
                        logger.error(f"  ❌ Error saving to MongoDB (page {page_num}): {e}")

                    # Save to Local
                    local_db.append(record)
                    save_local_db(local_db)
                    logger.info(f"  ✅ Page {page_num}: Đã lưu ({current_topic})")
                else:
                    logger.warning(f"  ⚠️  Page {page_num}: Invalid data or extraction failed")

                time.sleep(RATE_LIMIT_DELAY)

            doc.close()
            logger.info(f"✅ Finished processing {pdf_name}")
        except Exception as e:
            logger.error(f"❌ Error processing {pdf_name}: {e}", exc_info=True)

    logger.info(f"\n{'='*60}")
    logger.info("✅ Pipeline Finished!")
    logger.info(f"{'='*60}")


def validate_extracted_data(data: Dict[str, Any], page_num: int) -> bool:
    """Validate schema of extracted data."""
    required_fields = {
        "page_info": ["page_id", "type", "chapter", "topic"],
        "content_segments": [],
        "visual_analysis": [],
        "rich_metadata": ["summary", "keywords"]
    }
    
    try:
        # Check top-level fields
        if not isinstance(data, dict):
            logger.error(f"  ❌ Page {page_num}: data không phải dict")
            return False
        
        # Check page_info
        if "page_info" not in data:
            logger.error(f"  ❌ Page {page_num}: thiếu field 'page_info'")
            return False
        
        page_info = data["page_info"]
        for field in required_fields["page_info"]:
            if field not in page_info:
                logger.error(f"  ❌ Page {page_num}: page_info thiếu field '{field}'")
                return False
        
        # Check page_id match
        if page_info.get("page_id") != page_num:
            logger.warning(f"  ⚠️  Page {page_num}: page_id không khớp ({page_info.get('page_id')} vs {page_num})")
        
        # Check content_segments
        if "content_segments" not in data:
            logger.warning(f"  ⚠️  Page {page_num}: thiếu 'content_segments' (có thể là trang trống)")
        elif not isinstance(data["content_segments"], list):
            logger.error(f"  ❌ Page {page_num}: 'content_segments' không phải list")
            return False
        
        # Check visual_analysis
        if "visual_analysis" not in data:
            logger.warning(f"  ⚠️  Page {page_num}: thiếu 'visual_analysis'")
        elif not isinstance(data["visual_analysis"], list):
            logger.error(f"  ❌ Page {page_num}: 'visual_analysis' không phải list")
            return False
        
        # Check rich_metadata
        if "rich_metadata" not in data:
            logger.warning(f"  ⚠️  Page {page_num}: thiếu 'rich_metadata'")
        else:
            metadata = data["rich_metadata"]
            for field in required_fields["rich_metadata"]:
                if field not in metadata:
                    logger.warning(f"  ⚠️  Page {page_num}: rich_metadata thiếu field '{field}'")
        
        return True
    except Exception as e:
        logger.error(f"  ❌ Page {page_num}: Lỗi khi validate data: {e}")
        return False


def get_ultimate_ai_data(
    image_bytes: bytes, page_num: int, filename: str, last_chapter: str, last_topic: str
) -> Optional[Dict[str, Any]]:
    """Extract dữ liệu từ ảnh PDF page sử dụng Gemini Vision API."""
    if not extract_key_manager:
        logger.error(f"  ❌ Page {page_num}: Extract key_manager không được khởi tạo")
        return None
    
    try:
        prompt = HISTORY_PAGE_EXTRACTION_PROMPT.format(
            page_num=page_num,
            filename=filename,
            last_chapter=last_chapter,
            last_topic=last_topic,
        )
        image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")

        max_retries = len(API_KEYS) if API_KEYS else 1
        for attempt in range(max_retries):
            try:
                response = extract_key_manager.generate_content([prompt, image_part])
                
                # Check response.text exists
                if not hasattr(response, 'text') or not response.text:
                    logger.error(f"  ❌ Page {page_num}: Response không có text (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        time.sleep(RATE_LIMIT_RETRY_DELAY)
                        continue
                    return None
                
                # Check if response is too short (likely truncated)
                if len(response.text) < 100:
                    logger.warning(f"  ⚠️  Page {page_num}: Response quá ngắn ({len(response.text)} chars), có thể bị cắt cụt")
                    if attempt < max_retries - 1:
                        time.sleep(RATE_LIMIT_RETRY_DELAY)
                        continue
                
                # Parse JSON
                try:
                    parsed_data = _parse_response_text(response.text)
                    logger.debug(f"  ✅ Page {page_num}: Parse JSON thành công")
                    return parsed_data
                except json.JSONDecodeError as json_err:
                    logger.error(
                        f"  ❌ Page {page_num}: JSON decode error (attempt {attempt + 1}): {json_err}\n"
                        f"     Response text (first 500 chars): {response.text[:500]}"
                    )
                    if attempt < max_retries - 1:
                        time.sleep(RATE_LIMIT_RETRY_DELAY)
                        continue
                    return None
                    
            except Exception as e:
                error_str = str(e).lower()
                logger.warning(f"  ⚠️  Page {page_num}: Lỗi API (attempt {attempt + 1}): {e}")
                
                if ("429" in error_str or "quota" in error_str) and attempt < max_retries - 1:
                    time.sleep(RATE_LIMIT_RETRY_DELAY)
                    continue
                elif attempt < max_retries - 1:
                    time.sleep(RATE_LIMIT_RETRY_DELAY)
                    continue
                else:
                    logger.error(f"  ❌ Page {page_num}: Thất bại sau {max_retries} lần thử: {e}")
                    return None
        
        return None
    except Exception as e:
        logger.error(f"  ❌ Page {page_num}: Exception không mong đợi: {e}", exc_info=True)
        return None


def _parse_response_text(text: str) -> Dict[str, Any]:
    candidates: list[str] = []
    original = text.strip()
    candidates.append(original)

    # Remove trailing commas before } or ]
    no_trailing_commas = re.sub(r",\s*([}\]])", r"\1", original)
    candidates.append(no_trailing_commas)

    def _balance_brackets(s: str) -> str:
        open_curly = s.count("{")
        close_curly = s.count("}")
        open_square = s.count("[")
        close_square = s.count("]")

        if close_curly < open_curly:
            s += "}" * (open_curly - close_curly)
        if close_square < open_square:
            s += "]" * (open_square - close_square)
        return s

    candidates.append(_balance_brackets(no_trailing_commas))

    # Cut to last '}' if exists
    last_curly = no_trailing_commas.rfind("}")
    if last_curly != -1:
        candidates.append(_balance_brackets(no_trailing_commas[: last_curly + 1]))

    # If number of quotes is odd, add a quote to avoid unterminated string
    def _fix_quotes(s: str) -> str:
        if s.count('"') % 2 != 0:
            return s + '"'
        return s

    fixed_quote_candidates = []
    for c in candidates:
        fixed_quote_candidates.append(_fix_quotes(c))

    for candidate in fixed_quote_candidates + candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    # If still fails, throw error to caller to log and skip page
    raise json.JSONDecodeError("Unrecoverable JSON from model", original, 0)


def load_local_db():
    if not os.path.exists(OUTPUT_JSON):
        return []

    try:
        if os.path.getsize(OUTPUT_JSON) == 0:
            logger.warning(f"Local DB is empty: {OUTPUT_JSON}")
            return []

        with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        backup_path = f"{OUTPUT_JSON}.bak"
        try:
            os.replace(OUTPUT_JSON, backup_path)
            logger.warning(
                f"Local DB corrupted, backed up to {backup_path}. "
                f"Resetting to empty list. Error: {e}"
            )
        except OSError:
            logger.warning(
                f"Local DB corrupted and cannot be moved. "
                f"Proceeding with empty list. Error: {e}"
            )
        return []
    except IOError as e:
        logger.warning(f"Failed to load local DB: {e}")
        return []


def save_local_db(local_db):
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(local_db, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    process_ultimate_pipeline()