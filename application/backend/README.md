RahuSearch – Usage & Configuration Guide
=======================================

This project is designed to be mostly provider-agnostic.
Where possible, components can be changed via environment variables only.
Some components (DB, reranker) require explicit code changes by design.

--------------------------------------------------
1) DATABASE (SEARCH BACKEND)
--------------------------------------------------

Current backend:
- Weaviate (v4 collections API)

Related folders/files:
- backend/app/db/
  - base.py
  - weaviate_backend.py
- backend/app/pipeline/search_pipeline.py

Env configuration:
- WEAVIATE_URL
- WEAVIATE_CLASS

Code dependency:
- SearchPipeline explicitly instantiates the backend:

    backend = WeaviateBackend()

If you want to change the database (e.g. OpenSearch, Qdrant, etc.):
- You MUST:
  1) Implement a new backend by extending:
     backend/app/db/base.py → SearchBackend
  2) Change ONE line in:
     backend/app/pipeline/search_pipeline.py

This is an intentional design choice.
Database is NOT provider-agnostic by env only.

--------------------------------------------------
2) EMBEDDINGS (OPENAI-COMPATIBLE, PROVIDER-AGNOSTIC)
--------------------------------------------------

Embedding architecture:
- Backend talks ONLY to an OpenAI-compatible embeddings API
- Provider is completely abstracted away

Related folders/files:
- backend/app/embedding/
  - base.py
  - gateway_embedding.py
  - factory.py

Used class:
- GatewayEmbedding

Runtime behavior:
- The backend does NOT know:
  - Whether embeddings are local or external
  - Which provider is used
- It only knows:
  - EMBED_BASE_URL
  - EMBED_MODEL
  - EMBED_API_KEY

IMPORTANT:
- For this project, EMBED_RUNTIME is expected to be:
  
    EMBED_RUNTIME=external

- This means:
  - Embeddings are served by an external API
  - vLLM is NOT started
  - Backend behavior does NOT change

External provider example (OpenAI):
    EMBED_RUNTIME=external
    EMBED_BASE_URL=https://api.openai.com/v1
    EMBED_API_KEY=YOUR_KEY
    EMBED_MODEL=text-embedding-3-small

Local provider example (vLLM, OpenAI-compatible):
    EMBED_RUNTIME=local
    EMBED_BASE_URL=http://localhost:8001/v1
    EMBED_API_KEY=EMPTY
    EMBED_MODEL=intfloat/multilingual-e5-base

Code changes required?
- NO
- Changing provider or model is 100% env-based

--------------------------------------------------
3) VISION / IMAGE-TO-TEXT (OPENAI-COMPATIBLE CHAT API)
--------------------------------------------------

Current vision provider:
- OpenRouter

Related folders/files:
- backend/app/openrouter/
  - client.py
  - prompts.py
  - image_processor.py

Env configuration:
- IMAGE_TO_TEXT_MODEL
- OPENROUTER_API_KEY
- LLM_BASE_URL

How it works:
- ImageProcessor uses an OpenAI-compatible ChatCompletion API
- Sends image + structured system prompt
- Expects strict JSON output

Changing vision model:
- Just change:
  
    IMAGE_TO_TEXT_MODEL=...

Changing vision provider:
- Provider MUST expose OpenAI-compatible Chat API
- Update:
  
    LLM_BASE_URL
    OPENROUTER_API_KEY

Code changes required?
- NO, if provider is OpenAI-compatible
- YES, if provider is NOT OpenAI-compatible

--------------------------------------------------
4) RERANKER (NOT PROVIDER-AGNOSTIC)
--------------------------------------------------

Current reranker:
- FlagEmbedding
- Model: BAAI/bge-reranker-v2-m3
- Runs locally (CPU or GPU)

Related folders/files:
- backend/app/ranking/
  - reranker_processor.py

Env variables:
- RERANKER_MODEL (informational only)

Important notes:
- Reranker is NOT OpenAI-compatible
- Reranker is NOT swappable via env only
- This is intentional (performance + control)

If you want to change the reranker:
- You MUST modify code in:
  
    backend/app/ranking/reranker_processor.py

- Replace FlagReranker with your own implementation
- Keep the method signature recommended:

    rerank(query, docs)

Code changes required?
- YES (always)

--------------------------------------------------
5) QUICK SUMMARY
--------------------------------------------------

Component    | Folder                    | Env Only | Code Change
------------ | ------------------------- | -------- | -----------
Database     | app/db                    | NO       | YES
Embedding    | app/embedding             | YES      | NO
Vision       | app/openrouter + preprocess | YES*   | NO / MAYBE
Reranker     | app/ranking               | NO       | YES

* Vision requires code changes only if provider is not OpenAI-compatible.

--------------------------------------------------
6) RECOMMENDED USAGE
--------------------------------------------------

- Use EMBED_RUNTIME=external
- Swap embedding models freely via .env
- Swap vision models via .env
- Treat DB and reranker changes as explicit engineering tasks

This keeps the system stable, debuggable, and production-safe.
