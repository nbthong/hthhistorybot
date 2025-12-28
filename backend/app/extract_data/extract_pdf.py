import os
import fitz
import json
import time
import io
from typing import Optional, Dict, Any
from PIL import Image
from dotenv import load_dotenv
from app.services.key_manager_gemini import key_manager, API_KEYS
from app.utils.prompts import HISTORY_PAGE_EXTRACTION_PROMPT
from app.utils.config import (
    MAX_PAGES_PER_PDF,
    RATE_LIMIT_DELAY,
    RATE_LIMIT_RETRY_DELAY,
    PDF_ZOOM_MATRIX,
    DATA_DIR,
    OUTPUT_JSON,
    ENV_FILE,
)
from app.databases.database import get_collection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv(ENV_FILE)


def process_ultimate_pipeline() -> None:
    if not key_manager:
        logger.error("Key manager not initialized")
        return

    local_db = load_local_db()
    if not os.path.exists(DATA_DIR):
        return

    pdf_files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith(".pdf")])

    for pdf_name in pdf_files:
        logger.info(f"\n--- Processing: {pdf_name} ---")
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
                        f"  Page {page_num}: Exists. Context updated to: {current_topic}"
                    )
                    continue

                logger.info(
                    f"  Page {page_num}/{total_pages}: Extracting with context: {current_topic}"
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

                if ai_data:
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
                    get_collection().update_one(
                        {"doc_id": unique_id}, {"$set": record}, upsert=True
                    )

                    # Save to Local
                    local_db.append(record)
                    save_local_db(local_db)
                    logger.info(f"  Page {page_num}: ✅ Saved ({current_topic})")

                time.sleep(RATE_LIMIT_DELAY)

            doc.close()
        except Exception as e:
            logger.error(f"Error processing {pdf_name}: {e}")

    logger.info("\n✅ Pipeline Finished!")


def get_ultimate_ai_data(
    image_bytes: bytes, page_num: int, filename: str, last_chapter: str, last_topic: str
) -> Optional[Dict[str, Any]]:
    try:
        img = Image.open(io.BytesIO(image_bytes))
        prompt = HISTORY_PAGE_EXTRACTION_PROMPT.format(
            page_num=page_num,
            filename=filename,
            last_chapter=last_chapter,
            last_topic=last_topic,
        )

        max_retries = len(API_KEYS) if API_KEYS else 1
        for attempt in range(max_retries):
            try:
                model = key_manager.get_model()
                response = model.generate_content([prompt, img])
                return json.loads(response.text)
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    key_manager.switch_key()
                    time.sleep(RATE_LIMIT_RETRY_DELAY)
                    continue
                return None
        return None
    except Exception as e:
        logger.error(f"Error at page {page_num}: {e}")
        return None


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