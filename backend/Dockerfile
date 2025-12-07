# ------------------------------------------
# BASE IMAGE (CUDA + Ubuntu 22.04)
# ------------------------------------------
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

ARG DEBIAN_FRONTEND=noninteractive

# ------------------------------------------
# Install Python 3.11 (same as conda env)
# ------------------------------------------
RUN apt-get update && apt-get install -y \
    software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && apt-get install -y \
    python3.11 python3.11-distutils python3.11-dev curl && \
    rm -rf /var/lib/apt/lists/*

# python3.11'ı default python3 yapalım
RUN ln -sf /usr/bin/python3.11 /usr/bin/python3
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# ------------------------------------------
# WORKDIR
# ------------------------------------------
WORKDIR /app

# ------------------------------------------
# Install Python dependencies
# ------------------------------------------
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# GPU'lu torch yükle (CUDA 12.1)
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# ------------------------------------------
# Copy project
# ------------------------------------------
COPY . .

# ------------------------------------------
# Start API
# ------------------------------------------
CMD ["uvicorn", "app.api.api:app", "--host", "0.0.0.0", "--port", "8000"]
