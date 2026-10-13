import os
import time
import logging
from google import genai

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        # Assumes GEMINI_API_KEY is set in the environment
        if os.environ.get("GEMINI_API_KEY"):
            self.client = genai.Client()
        else:
            self.client = None
        self.model = "gemini-3.8-flash"

    def generate(self, prompt: str, max_retries: int = 3) -> str:
        if not self.client:
            return "Error: GEMINI_API_KEY is not set in the environment. Please add it to your .env file."

        delays = [2, 4, 8]
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                )
                return response.text
            except Exception as e:
                last_exception = e
                err_str = str(e).lower()
                is_transient = (
                    "503" in err_str
                    or "unavailable" in err_str
                    or "resourceexhausted" in err_str
                    or "rate limit" in err_str
                    or "429" in err_str
                )

                if is_transient and attempt < max_retries:
                    delay = delays[attempt] if attempt < len(delays) else delays[-1]
                    logger.warning(f"Gemini API transient failure (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                else:
                    break

        return f"Error generating response: {str(last_exception)}"

