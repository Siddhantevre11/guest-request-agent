"""Real entrypoint: `uvicorn app.server:app --reload` (requires OPENAI_API_KEY)."""

from .llm_openai import OpenAILLMClient
from .main import create_app

app = create_app(OpenAILLMClient())
