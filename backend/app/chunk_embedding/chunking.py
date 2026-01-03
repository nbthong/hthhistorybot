import logging
from typing import List

from app.utils.config import CHUNK_OVERLAP, CHUNK_SIZE

logger = logging.getLogger(__name__)


def chunk_text(text: str) -> List[str]:
    normalized = " ".join((text or "").split())
    if len(normalized) <= CHUNK_SIZE:
        return [normalized]

    chunks: List[str] = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + CHUNK_SIZE)
        chunk = normalized[start:end]
        chunks.append(chunk)
        if end == len(normalized):
            break
        start = max(0, end - CHUNK_OVERLAP)
    return chunks



