# ---------------------------------------------
# BACKEND DOCKERFILE (FASTAPI - CPU ONLY)
# ---------------------------------------------
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# (İhtiyaç olursa genişletirsin)
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# deps
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# code
COPY backend /app

EXPOSE 8000

# Not: app.main içinde uvicorn çalıştırıyorsan bu OK
# Eğer uvicorn:app diye çalışıyorsan CMD'i değiştiririz.
CMD ["python", "-m", "app.main"]
