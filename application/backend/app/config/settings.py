import os
from dotenv import load_dotenv

load_dotenv()

# -----------------------------------------------------
# DATA
# -----------------------------------------------------
DATA_ROOT = os.getenv("DATA_ROOT")

# -----------------------------------------------------
# EMBEDDING (OPENAI-COMPATIBLE, KOŞULSUZ)
# -----------------------------------------------------
EMBED_BASE_URL = os.getenv("EMBED_BASE_URL")
EMBED_API_KEY = os.getenv("EMBED_API_KEY", "EMPTY")
EMBED_MODEL = os.getenv("EMBED_MODEL")

if not EMBED_BASE_URL:
    raise RuntimeError("EMBED_BASE_URL is required")
if not EMBED_MODEL:
    raise RuntimeError("EMBED_MODEL is required")


# -----------------------------------------------------
# RERANKER
# -----------------------------------------------------
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")
RERANK_CANDIDATE_LIMIT = int(os.getenv("RERANK_CANDIDATE_LIMIT", 48))


# -----------------------------------------------------
# IMAGE → TEXT
# -----------------------------------------------------
IMAGE_TO_TEXT_MODEL = os.getenv("IMAGE_TO_TEXT_MODEL", "gpt-4o-mini")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")

# -----------------------------------------------------
# OPENAI (NON-EMBEDDING)
# -----------------------------------------------------
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_CLASS = os.getenv("WEAVIATE_CLASS")
