FROM python:3.11-slim

WORKDIR /app

# ----------------------------
# System deps
# ----------------------------
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# ----------------------------
# HuggingFace cache (IMPORTANT)
# ----------------------------
ENV HF_HOME=/root/.cache/huggingface
ENV TRANSFORMERS_CACHE=/root/.cache/huggingface
ENV TORCH_HOME=/root/.cache/torch

# ----------------------------
# Python deps
# ----------------------------
COPY pre_deploy/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ----------------------------
# 🔥 PRELOAD MODEL (ASIL FARK)
# ----------------------------
RUN python - <<EOF
from sentence_transformers import SentenceTransformer
print("⏳ Preloading model: intfloat/e5-large")
SentenceTransformer("intfloat/e5-large")
print("✅ Model cached successfully")
EOF

# ----------------------------
# Predeploy code
# ----------------------------
COPY pre_deploy /app

# ----------------------------
# Run once
# ----------------------------
CMD ["python", "-m", "opensearch_client"]
