import os
from google import genai

class LLMClient:
    def __init__(self):
        # Assumes GEMINI_API_KEY is set in the environment
        self.client = genai.Client()
        self.model = "gemini-2.5-flash"

    def generate(self, prompt: str) -> str:
        if not os.environ.get("GEMINI_API_KEY"):
            return "Error: GEMINI_API_KEY is not set in the environment."
            
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            return f"Error generating response: {str(e)}"
