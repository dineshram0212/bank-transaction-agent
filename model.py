import os
from openai import OpenAI

class Model:
    def __init__(self, base_url="https://api.groq.com/openai/v1"):
        self.api_key = os.getenv("LLM_API_KEY")
        self.client = OpenAI(
            base_url=base_url,
            api_key=self.api_key
        )
