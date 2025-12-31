from openai import OpenAI
from app.config.settings import OPENROUTER_API_KEY, LLM_BASE_URL

def get_openrouter_client() -> OpenAI:
    return OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=LLM_BASE_URL,
    )
