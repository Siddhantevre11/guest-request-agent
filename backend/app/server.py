"""Real entrypoint: `uvicorn app.server:app --reload` (requires OPENAI_API_KEY)."""

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

from .llm_openai import OpenAILLMClient  # noqa: E402
from .main import create_app  # noqa: E402

app = create_app(OpenAILLMClient())
