FROM python:3.11-slim

WORKDIR /app

# Sistem bağımlılıkları (torch için gerekebiliyor)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY pre_deploy/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Predeploy kodu
COPY pre_deploy /app

# Varsayılan komut
CMD ["python", "-m", "opensearch_client"]
