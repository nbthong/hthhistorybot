import os
import logging
from typing import List, Any
from dotenv import load_dotenv
import google.generativeai as genai
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
        self.model_id: str = PREFERRED_MODEL.replace("models/", "")
        self.generation_config = GENERATION_CONFIG

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
        self.model = self._setup_model(self.keys[0])

    def _setup_model(self, key: str) -> Any:
        """Setup model với API key được chỉ định."""
        genai.configure(api_key=key)
        return genai.GenerativeModel(
            model_name=self.model_id, generation_config=self.generation_config
        )

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

        self.model = self._setup_model(new_key)
        return True

    def get_model(self) -> Any:
        return self.model


if API_KEYS:
    key_manager = GeminiKeyManager(API_KEYS)
else:
    key_manager = None
    logging.warning("No API keys found in environment variables!")