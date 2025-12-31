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
# Python deps
# ----------------------------
COPY pre_deploy/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ----------------------------
# Predeploy code
# ----------------------------
COPY pre_deploy /app

# ----------------------------
# Run once (index + embedding)
# ----------------------------
CMD ["python", "-m", "opensearch_client"]
