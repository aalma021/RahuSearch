# Requirements
To run this project, the following components must be installed:

1) CUDA (optional – only needed if the system has an NVIDIA GPU for acceleration)
   Download (official NVIDIA page):
   https://developer.nvidia.com/cuda-downloads

2) Docker and Docker Compose (required for running the OpenSearch cluster)
   Download Docker:
   https://docs.docker.com/engine/install/
   Docker Compose installation guide:
   https://docs.docker.com/compose/install/

3) Conda (Python environment management – the project uses Python 3.11)
   Download Miniconda (recommended):
   https://docs.conda.io/en/latest/miniconda.html

4) Make (required for running automation commands such as `make all`)
   On Ubuntu you can install it with:
       sudo apt install make

# Pipeline Overview
The system works in the following steps:
- Input Router: If the user inputs an image, GPT-Vision converts it into descriptive text. If the input is text, it is sent directly to the text pipeline.
- Retrieval Pipeline:
    - BM25 for text relevance
    - E5 embedding for semantic similarity
    - Hybrid merge (BM25 + vector score)
    - BGE Reranker for the final ordering
- Output: A ranked list of the most relevant products in JSON format (title, price, url, brand, image, score).

# Pre-Deploy (Indexing)
This step loads and indexes the dataset into the OpenSearch cluster:
- Reads all product files
- Removes duplicate entries
- Builds the combined text field
- Generates E5 embeddings
- Writes everything into the OpenSearch index
This step is executed only once.

# Usage

## 1) Pre-Deploy (ONE-TIME Setup)
This step prepares your dataset and uploads it into the OpenSearch cluster.

1) Open a terminal and navigate into the `pre-deploy` folder.
2) Edit the `.env` file and update `DATA_ROOT` with the full path to your dataset directory.
3) Run:
   make all
This will create the OpenSearch cluster and index all data into it.  
You only need to run this step once unless the dataset changes.

---

## 2) Backend API (Run Application Anytime)
After pre-deploy has been completed once, you can run the backend/API whenever you want.

1) Navigate into the `project` folder.
2) Run:
   make all
This will:
- Start the OpenSearch container
- Wait until OpenSearch is ready
- Activate the conda environment
- Launch the FastAPI backend

After the API is running, open:
http://localhost:8000/docs
to test image and text search functionalities.

---
