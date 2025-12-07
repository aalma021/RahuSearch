import os
from dotenv import load_dotenv

# Load .env file (root or current directory)
load_dotenv()

# -----------------------------
# OpenSearch Settings
# -----------------------------
OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "http://localhost:9200")
OPENSEARCH_INDEX = os.getenv("OPENSEARCH_INDEX", "products")
OPENSEARCH_PASSWORD = os.getenv("OPENSEARCH_PASSWORD", "MyStrongPassword123!")

# -----------------------------
# Embedding Model (E5 / BGE etc.)
# -----------------------------
EMBED_MODEL = os.getenv("EMBED_MODEL", "intfloat/e5-large")

# -----------------------------
# Reranker Model
# -----------------------------
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")

# CANDIDATE_LIMIT:
#   Maximum number of documents passed to the cross-encoder reranker.
#   Instead of reranking all hybrid (BM25 + Vector) results, only the top N
#   candidates are reranked to balance latency and accuracy. (Recommended: 32–64)
CANDIDATE_LIMIT = int(os.getenv("RERANK_CANDIDATE_LIMIT", 48))

# -----------------------------
# GPT Image-to-Text Model
# Used only if image is uploaded
# -----------------------------
IMAGE_TO_TEXT_MODEL = os.getenv("IMAGE_TO_TEXT_MODEL", "gpt-4o-mini")

# -----------------------------
# OpenAI API Key
# -----------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# -----------------------------
# DATA_ROOT for images
# -----------------------------
DATA_ROOT = os.getenv("DATA_ROOT")
