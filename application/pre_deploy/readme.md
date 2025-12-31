Predeploy Pipeline (OpenSearch + Embedding Preparation)

This module prepares all product data before loading it into an OpenSearch cluster.
It automatically scans a root directory, processes every JSONL file inside category folders, normalizes the fields, generates multilingual search text, extracts image metadata, creates a combined_text field, produces semantic embeddings, deduplicates documents, and finally loads everything into OpenSearch.

The goal is to provide the user with a single command (make all) that launches OpenSearch, processes all data, and indexes the results.

Features

Automatically finds all *.jsonl files under the provided DATA_ROOT directory

Supports unlimited vendors (Jarir, Noon, Almanea, Extra…) without modifying the code

Builds English and Arabic search indices (text_search_en / text_search_ar)

Extracts and flattens img_to_text attributes

Generates a unified combined_text field tuned for semantic search

Deduplicates documents using multiple strategies (id → store+url → combined_text)

Automatically selects GPU if CUDA is available

Uses OpenSearch bulk indexing with upsert semantics

Fully environment-driven (zero hardcoded paths)

Requirements

Ubuntu or WSL (recommended)

Docker installed and running

Conda installed

environment.yml and Makefile included in the project

A .env.local file created by the user

GPU is optional; CPU works fine.

Environment Configuration (.env.local)

Example configuration:

DATA_ROOT=/mnt/c/Users/AkifC/OneDrive/Masaüstü/upwork/data/jarir
OPENSEARCH_URL=http://localhost:9200

OPENSEARCH_INDEX=products
EMBED_MODEL=intfloat/e5-large
EMBED_DIM=1024

DATA_ROOT Explanation:
You only need to provide the parent folder containing all category folders. For example, if your structure is:

jarir/Headphones/.jsonl
jarir/Laptops/.jsonl
jarir/Tablets/*.jsonl

then simply set:

DATA_ROOT=/path/to/jarir

The system will recursively scan all .jsonl files inside all subdirectories.

Usage
1. Create Conda environment

make env

2. Start local OpenSearch cluster

make up

3. Run preprocessing + embedding generation + bulk upload

make seed

What this step does:

Scans all JSONL files inside DATA_ROOT

Builds text_search_en, text_search_ar, and image_text

Generates combined_text

Deduplicates documents

Generates embeddings (GPU or CPU automatically)

Sends everything to OpenSearch in bulk

4. One-Shot: Run all steps

make all (env + up + seed)

5. Reset OpenSearch completely (removes volumes)

make reset

Notes

The index is created automatically if it doesn't exist

Re-running the pipeline is safe: _id is used as the primary key, so documents with the same ID are updated

The same pipeline works on Linux, WSL, or Windows (through WSL)

No Python paths need to be edited; everything is controlled by .env.local