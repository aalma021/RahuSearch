# ------------------------------------------
# BASE IMAGE (CPU ONLY)
# ------------------------------------------
FROM python:3.11-slim

WORKDIR /app

# ------------------------------------------
# System deps (minimal)
# ------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# ------------------------------------------
# Requirements
# ------------------------------------------
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# ------------------------------------------
# Do NOT install GPU packages
# Torch CPU'su yeter
# ------------------------------------------
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# ------------------------------------------
# Copy project
# ------------------------------------------
COPY . .

# ------------------------------------------
# Start FastAPI
# ------------------------------------------
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
