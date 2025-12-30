import os
import logging
from typing import Iterable, List, Any
from dotenv import load_dotenv
from google import genai
from app.utils.config import PREFERRED_MODEL, GENERATION_CONFIG, ENV_FILE

load_dotenv(ENV_FILE)

api_keys_str = os.getenv("GOOGLE_API_KEYS") or os.getenv("GOOGLE_API_KEY", "")
API_KEYS = [k.strip() for k in api_keys_str.split(",") if k.strip()]


class GeminiKeyManager:
    def __init__(self, keys: List[str]):
        if not keys:
            raise ValueError("API keys list cannot be empty!")

        self.keys: List[str] = keys
        self.current_index: int = 0
        self.model_id: str = PREFERRED_MODEL
        self.generation_config: dict[str, Any] = GENERATION_CONFIG

        unique_keys = set(keys)
        if len(unique_keys) < len(keys):
            logging.warning(
                f"Detected {len(keys) - len(unique_keys)} duplicate Gemini API key(s). "
                f"Unique keys in use: {len(unique_keys)}"
            )

        logging.info(
            f"Initialized GeminiKeyManager with {len(unique_keys)} unique API key(s), "
            f"using model: {self.model_id}"
        )
        self.client = self._setup_client(self.keys[0])

    def _setup_client(self, key: str) -> genai.Client:
        """Setup genai.Client với API key được chỉ định."""
        return genai.Client(api_key=key)

    def switch_key(self) -> bool:
        """Chuyển sang API key tiếp theo trong danh sách."""
        if not self.keys:
            logging.error("No API keys configured")
            return False

        previous_index = self.current_index
        self.current_index = (self.current_index + 1) % len(self.keys)
        new_key = self.keys[self.current_index]

        logging.info(
            f"Switching Gemini API key: #{previous_index + 1} → #{self.current_index + 1} "
            f"({new_key[:8]}...{new_key[-8:]})"
        )

        self.client = self._setup_client(new_key)
        return True

    def generate_content(self, contents: Any, **kwargs: Any):
        return self.client.models.generate_content(
            model=self.model_id,
            contents=contents,
            config=self.generation_config,
            **kwargs,
        )

    def stream_content(self, contents: Any, **kwargs: Any) -> Iterable[str]:
        stream = self.client.models.generate_content_stream(
            model=self.model_id,
            contents=contents,
            config=self.generation_config,
            **kwargs,
        )
        for chunk in stream:
            text = getattr(chunk, "text", None)
            if not text and getattr(chunk, "candidates", None):
                # Fallback: một số chunk có thể không set chunk.text
                try:
                    parts = chunk.candidates[0].content.parts or []
                    text = "".join(
                        [getattr(p, "text", "") for p in parts if getattr(p, "text", None)]
                    )
                except Exception:
                    text = None
            if text:
                yield text


if API_KEYS:
    key_manager = GeminiKeyManager(API_KEYS)
else:
    key_manager = None
    logging.warning("No API keys found in environment variables!")