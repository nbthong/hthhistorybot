import os
import logging
import time
from typing import Iterable, List, Any, Optional
from dotenv import load_dotenv
from google import genai
from app.utils.config import PREFERRED_MODEL, GENERATION_CONFIG, ENV_FILE

load_dotenv(ENV_FILE)

api_keys_str = os.getenv("GOOGLE_API_KEYS") or os.getenv("GOOGLE_API_KEY", "")
API_KEYS = [k.strip() for k in api_keys_str.split(",") if k.strip()]

class GeminiKeyManager:
    def __init__(
        self,
        keys: List[str],
        model_id: Optional[str] = None,
        generation_config: Optional[dict[str, Any]] = None,
        retry_attempts: int = 1,
        retry_delay: float = 1.0,
    ):
        if not keys:
            raise ValueError("API keys list cannot be empty!")

        self.keys: List[str] = keys
        self.model_id: str = model_id or PREFERRED_MODEL
        self.generation_config: dict[str, Any] = generation_config or GENERATION_CONFIG
        self.retry_attempts = max(0, retry_attempts)
        self.retry_delay = max(0.0, retry_delay)

        unique_keys = set(keys)
        logging.info(f"Initialized GeminiKeyManager with {len(unique_keys)} unique API keys.")
        self.client = self._setup_client(self.keys[0])

    def _setup_client(self, key: str) -> genai.Client:
        return genai.Client(api_key=key)

    def generate_content(self, contents: Any, **kwargs: Any):
        """Gọi model với retry nhẹ trên cùng một key khi gặp lỗi tạm thời."""
        for attempt in range(self.retry_attempts + 1):
            try:
                return self.client.models.generate_content(
                    model=self.model_id,
                    contents=contents,
                    config=self.generation_config,
                    **kwargs,
                )
            except Exception as e:
                error_str = str(e).lower()
                if ("429" in error_str or "quota" in error_str) and attempt < self.retry_attempts:
                    logging.warning(f"⚠️ Lỗi 429/quota (attempt {attempt + 1}/{self.retry_attempts + 1}), retry sau {self.retry_delay}s")
                    time.sleep(self.retry_delay)
                    continue
                raise e
        
        raise Exception("⚡ Tất cả API Keys đều đã hết hạn mức sử dụng (429)!")

    def stream_content(self, contents: Any, **kwargs: Any) -> Iterable[str]:
        """Stream with light retry on the same key when initialization error occurs."""
        for attempt in range(self.retry_attempts + 1):
            try:
                stream = self.client.models.generate_content_stream(
                    model=self.model_id,
                    contents=contents,
                    config=self.generation_config,
                    **kwargs,
                )
                
                for chunk in stream:
                    text = getattr(chunk, "text", None)
                    if not text and getattr(chunk, "candidates", None):
                        try:
                            parts = chunk.candidates[0].content.parts or []
                            text = "".join([getattr(p, "text", "") for p in parts if getattr(p, "text", None)])
                        except Exception:
                            text = None
                    if text:
                        yield text
                return # Exit function after completing stream

            except Exception as e:
                error_str = str(e).lower()
                if ("429" in error_str or "quota" in error_str) and attempt < self.retry_attempts:
                    logging.warning(f"⚠️ Lỗi 429/quota khi khởi tạo stream (attempt {attempt + 1}/{self.retry_attempts + 1}), retry sau {self.retry_delay}s")
                    time.sleep(self.retry_delay)
                    continue
                raise e

if API_KEYS:
    key_manager = GeminiKeyManager(API_KEYS)
else:
    key_manager = None
    logging.warning("No API keys found!")