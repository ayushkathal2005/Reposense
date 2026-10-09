import os
from google import genai

class LLMClient:
    def __init__(self):
        # Assumes GEMINI_API_KEY is set in the environment
        if os.environ.get("GEMINI_API_KEY"):
            self.client = genai.Client()
        else:
            self.client = None
        self.model = "gemini-3.8-flash"

    def generate(self, prompt: str) -> str:
        if not self.client:
            return "Error: GEMINI_API_KEY is not set in the environment. Please add it to your .env file."
            
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            return f"Error generating response: {str(e)}"
