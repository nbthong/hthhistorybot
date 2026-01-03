from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.utils.config import OUTPUT_JSON_CHUNK_EMBEDDING_TEST, OUTPUT_JSON_CHUNK_EMBEDDING, OUTPUT_JSON_DATA, OUTPUT_JSON_DATA_TEST, CHUNK_SIZE, CHUNK_OVERLAP

logger = logging.getLogger(__name__)


_RE_LESSON_NUMBER = re.compile(r"\bBài\s*(\d+)\b", flags=re.IGNORECASE)


def _normalize_text(s: str) -> str:
    return " ".join((s or "").strip().lower().split())

def _parse_lesson_number(topic: str | None) -> Optional[int]:
    if not topic:
        return None
    m = _RE_LESSON_NUMBER.search(topic)
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None

def _safe_get_page_info(page_record: Dict[str, Any]) -> Dict[str, Any]:
    data = page_record.get("data") or {}
    page_info = data.get("page_info") or {}
    return page_info

def _format_segment_text(seg: Dict[str, Any]) -> str:
    heading = (seg.get("heading") or "").strip()
    text = (seg.get("text") or "").strip()
    table_md = (seg.get("table_markdown") or "").strip()

    parts: List[str] = []
    if heading:
        parts.append(heading)
    if text:
        parts.append(text)
    if table_md:
        parts.append(table_md)

    return "\n".join(parts).strip()

def _format_visual_item(item: Dict[str, Any]) -> Optional[str]:
    desc = (item.get("description") or "").strip()
    if desc:
        return f"[Hình ảnh]: {desc}"

    content = (item.get("content") or "").strip()
    if content:
        return f"[Hình ảnh]: {content}"

    return None

def _build_merged_text(page_records: List[Dict[str, Any]]) -> Tuple[str, int, int]:
    blocks: List[str] = []
    seg_count = 0
    vis_count = 0

    for rec in page_records:
        data = rec.get("data") or {}
        for seg in data.get("content_segments", []) or []:
            seg_text = _format_segment_text(seg)
            if len(seg_text.strip()) <= 0:
                continue
            seg_count += 1
            blocks.append(seg_text)

        for vis in data.get("visual_analysis", []) or []:
            vis_text = _format_visual_item(vis)
            if not vis_text:
                continue
            vis_count += 1
            blocks.append(vis_text)

    merged = "\n\n".join(blocks).strip()
    return merged, seg_count, vis_count


@dataclass(frozen=True)
class LessonGroupKey:
    source: str
    lesson_number: Optional[int]
    normalized_topic: str

    def to_lesson_key(self) -> str:
        if self.lesson_number is not None:
            return f"{self.source}::bai::{self.lesson_number}"
        return f"{self.source}::topic::{self.normalized_topic or 'undetermined'}"

def merge_lessons_from_history_db(
    history_db_path: str | Path,
    *,
    include_non_content_pages: bool = False,
) -> Dict[str, Any]:
    raw: Any
    with open(history_db_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if not isinstance(raw, list):
        raise ValueError(f"Unexpected schema: expected list, got {type(raw)}")

    raw_sorted: List[Dict[str, Any]] = sorted(
        (r for r in raw if isinstance(r, dict)),
        key=lambda r: (str(r.get("source", "")), int(r.get("page_id", 0))),
    )

    grouped: Dict[LessonGroupKey, List[Dict[str, Any]]] = {}

    for rec in raw_sorted:
        page_info = _safe_get_page_info(rec)
        page_type = str(page_info.get("type") or "").strip().upper()
        if not include_non_content_pages and page_type != "CONTENT":
            continue

        source = str(rec.get("source") or "").strip() or "UnknownSource"
        topic = str(page_info.get("topic") or "").strip() or "Undetermined"
        norm_topic = _normalize_text(topic)
        lesson_no = _parse_lesson_number(topic)

        key = LessonGroupKey(source=source, lesson_number=lesson_no, normalized_topic=norm_topic)
        grouped.setdefault(key, []).append(rec)

    # Build output lessons (sorted by source + lesson_number + topic)
    lessons: List[Dict[str, Any]] = []
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")

    for key in sorted(
        grouped.keys(),
        key=lambda k: (k.source, k.lesson_number if k.lesson_number is not None else 10**9, k.normalized_topic),
    ):
        pages = grouped[key]
        first_info = _safe_get_page_info(pages[0])
        chapter = str(first_info.get("chapter") or "Undetermined").strip() or "Undetermined"
        topic = str(first_info.get("topic") or "Undetermined").strip() or "Undetermined"

        merged_text, seg_count, vis_count = _build_merged_text(pages)
        if not merged_text:
            continue

        page_ids: List[int] = [int(p.get("page_id", 0)) for p in pages]
        doc_ids: List[str] = [str(p.get("doc_id", "")) for p in pages if p.get("doc_id")]

        lesson_number = key.lesson_number
        lesson_label = f"Bài {lesson_number}" if lesson_number is not None else "Undetermined"

        lessons.append(
            {
                "source": key.source,
                "lesson_key": key.to_lesson_key(),
                "lesson_label": lesson_label,
                "lesson_number": lesson_number,
                "chapter": chapter,
                "topic": topic,
                "page_ids": page_ids,
                "doc_ids": doc_ids,
                "merged_text": merged_text,
                "content_segments_count": seg_count,
                "visual_items_count": vis_count,
                "created_at": now_str,
            }
        )

    out: Dict[str, Any] = {
        "generated_at": now_str,
        "chunking": {"chunk_size": CHUNK_SIZE, "chunk_overlap": CHUNK_OVERLAP},
        "count": len(lessons),
        "lessons": lessons,
    }
    return out

def _convert_numpy_types(obj: Any) -> Any:
    """Recursively convert numpy types to Python native types for JSON serialization."""
    import numpy as np
    
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: _convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_convert_numpy_types(item) for item in obj]
    return obj

def save_merge_content_json(merged: Dict[str, Any], output_path: str | Path) -> None:
    """Save merged content to JSON file, converting numpy types to Python native types."""
    # Convert numpy types before saving
    merged_clean = _convert_numpy_types(merged)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(merged_clean, f, ensure_ascii=False, indent=2)

def run(
    *,
    history_db_path: str | Path = OUTPUT_JSON_DATA,
    merge_output_path: str | Path = OUTPUT_JSON_CHUNK_EMBEDDING_TEST,
    include_non_content_pages: bool = False,
) -> Dict[str, Any]:

    merged = merge_lessons_from_history_db(
        history_db_path,
        include_non_content_pages=include_non_content_pages,
    )
    save_merge_content_json(merged, merge_output_path)
    
    logger.info(f"Merged {merged.get('count', 0)} lessons and saved to {merge_output_path}")
    logger.info("To embed, run: python -m app.chunk_embedding.embedder")
    
    return merged

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)
    run(include_non_content_pages=False)
