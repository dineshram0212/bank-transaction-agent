import os
from openai import OpenAI

class Model:
    def __init__(self, base_url=None):
        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = base_url or os.getenv("BASE_URL", "https://api.groq.com/openai/v1")
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
