import os
import logging
from typing import Iterable, Any, Optional
from dotenv import load_dotenv
from google import genai
from app.utils.config import PREFERRED_MODEL, GENERATION_CONFIG, ENV_FILE

load_dotenv(ENV_FILE)

API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()

class GeminiKeyManager:
    def __init__(
        self,
        api_key: str,
        model_name: Optional[str] = None,
        generation_config: Optional[dict[str, Any]] = None,
    ):
        if not api_key:
            raise ValueError("API key cannot be empty!")

        self.model_name: str = model_name or PREFERRED_MODEL
        self.generation_config: dict[str, Any] = generation_config or GENERATION_CONFIG
        self.client = genai.Client(api_key=api_key)

    def _extract_text_from_chunk(self, chunk: Any) -> Optional[str]:
        """Extract text from chunk optimally."""
        if text := getattr(chunk, "text", None):
            return text
        try:
            parts = chunk.candidates[0].content.parts or []
            return "".join(p.text for p in parts if getattr(p, "text", None))
        except (AttributeError, IndexError, TypeError):
            return None

    def generate_content(self, contents: Any, **kwargs: Any):
        """Call model to generate content."""
        return self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=self.generation_config,
            **kwargs,
        )

    def stream_content(self, contents: Any, **kwargs: Any) -> Iterable[str]:
        """Stream content from model."""
        stream = self.client.models.generate_content_stream(
            model=self.model_name,
            contents=contents,
            config=self.generation_config,
            **kwargs,
        )
        for chunk in stream:
            if text := self._extract_text_from_chunk(chunk):
                yield text

if API_KEY:
    key_manager = GeminiKeyManager(API_KEY)
else:
    key_manager = None
    logging.warning("No API key found! Please set GOOGLE_API_KEY in environment variables.")