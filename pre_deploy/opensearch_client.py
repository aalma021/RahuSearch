"""
FINAL PRODUCTION PIPELINE
JSONL → normalize → image_to_text flatten → EN/AR search fields →
combined_text → dedupe → embedding → OpenSearch bulk upload
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Iterable, Optional, Tuple

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from opensearchpy import OpenSearch, helpers
import numpy as np
import torch
import uuid   # NEW: for fallback ID creation

# ---------------------------------------------------
# BASE DIR & ENV
# ---------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

load_dotenv(BASE_DIR / ".env.local")


# ---------------------------------------------------
# LOGGING
# ---------------------------------------------------
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

def log_info(x): print(f"{BLUE}[INFO] {x}{RESET}")
def log_success(x): print(f"{GREEN}[SUCCESS] {x}{RESET}")
def log_warn(x): print(f"{YELLOW}[WARN] {x}{RESET}")
def log_error(x): print(f"{RED}[ERROR] {x}{RESET}")


# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------
DATA_ROOT = Path(os.getenv("DATA_ROOT"))
OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "http://localhost:9200")
OPENSEARCH_INDEX = os.getenv("OPENSEARCH_INDEX")

EMBED_MODEL_NAME = os.getenv("EMBED_MODEL")

# REMOVE old EMBED_DIM environment requirement
# EMBED_DIM = int(os.getenv("EMBED_DIM"))

OPENSEARCH_PASSWORD = os.getenv("OPENSEARCH_PASSWORD")
if not OPENSEARCH_PASSWORD:
    raise ValueError("OPENSEARCH_PASSWORD is required in .env.local")

device = "cuda" if torch.cuda.is_available() else "cpu"
log_info(f"Device selected: {device}")


# ---------------------------------------------------
# BASIC HELPERS
# ---------------------------------------------------
def dedup_words(text: str) -> str:
    if not text:
        return ""
    out, seen = [], set()
    for w in text.split():
        k = w.lower()
        if k not in seen:
            out.append(w)
            seen.add(k)
    return " ".join(out)


def extract_image_text(prod: Dict[str, Any]) -> str:
    items = prod.get("img_to_text") or []
    parts = []

    for it in items:
        if not isinstance(it, dict):
            continue

        sc = it.get("short_caption")
        if sc: parts.append(sc)

        vk = it.get("visual_keywords")
        if isinstance(vk, list): parts.extend(vk)

        attrs = it.get("attributes") or {}
        if isinstance(attrs, dict):
            for key in ("product_type", "main_color", "secondary_color"):
                v = attrs.get(key)
                if v: parts.append(str(v))

            for key in ("style", "category_hint", "special_features", "visible_text"):
                v = attrs.get(key)
                if isinstance(v, list):
                    parts.extend(str(x) for x in v if x)
                elif isinstance(v, str):
                    parts.append(v)

    return " ".join(parts)


def build_search_text_en(doc: Dict[str, Any]) -> str:
    parts = [
        doc.get("brand"),
        doc.get("title_en"),
        doc.get("category_en"),
        doc.get("text_en"),
        doc.get("text_search")
    ]
    parts.extend(doc.get("tags_en") or [])
    return dedup_words(" ".join(str(p) for p in parts if p))


def build_search_text_ar(doc: Dict[str, Any]) -> str:
    parts = [
        doc.get("title_ar"),
        doc.get("category_ar"),
        doc.get("text_ar"),
        doc.get("text_search_ar")
    ]
    parts.extend(doc.get("tags_ar") or [])
    return dedup_words(" ".join(str(p) for p in parts if p))


def build_combined_text(doc, en, ar, image_text):
    parts = [
        doc.get("brand") or "",
        doc.get("store") or "",
        doc.get("product_group") or "",
        doc.get("category_en") or "",
        doc.get("category_ar") or "",
        en,
        ar,
        image_text,
    ]
    return dedup_words(" ".join(p.strip() for p in parts if p))


# ---------------------------------------------------
# DEDUP KEYS
# ---------------------------------------------------
def make_dedupe_key(doc: Dict[str, Any]) -> Optional[Tuple]:
    if doc.get("id"):
        return ("id", str(doc["id"]))

    if doc.get("store") and doc.get("url"):
        return ("store_url", str(doc["store"]), str(doc["url"]))

    if doc.get("combined_text"):
        return ("combined_text", doc["combined_text"])

    return None


def dedupe_docs(docs: List[Dict[str, Any]]):
    seen = set()
    out = []
    for d in docs:
        key = make_dedupe_key(d)
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        out.append(d)
    log_info(f"Dedup: {len(docs)} → {len(out)}")
    return out


# ---------------------------------------------------
# RAW FILES
# ---------------------------------------------------
def iter_raw_documents():
    log_info(f"Scanning JSONL files under {DATA_ROOT} ...")

    for path in DATA_ROOT.rglob("*.jsonl"):
        group = path.parent.name
        log_info(f"Reading: {path}")

        for line in path.open("r", encoding="utf-8"):
            if not line.strip():
                continue

            try:
                clean_line = line.replace("\ufeff", "").strip()
                raw = json.loads(clean_line)
            except Exception as e:
                print("BROKEN JSON LINE →", repr(clean_line[:200]))
                raise e

            images = raw.get("image_urls") or []
            image_url = images[0] if images else None

            doc = {
                "id": str(raw.get("id")),
                "store": raw.get("store") or "Jarir",
                "product_group": group,
                "url": raw.get("url") or raw.get("url_en"),
                "brand": raw.get("brand"),

                # PRICE FIX
                "price_final": raw.get("price_sar") or raw.get("price_aed") or None,
                "currency": "SAR" if raw.get("price_sar") else ("AED" if raw.get("price_aed") else None),

                "title_en": raw.get("title_en"),
                "title_ar": raw.get("title_ar"),

                "category_en": raw.get("category_en") or raw.get("category"),
                "category_ar": raw.get("category_ar"),

                "tags_en": raw.get("tags_en") or [],
                "tags_ar": raw.get("tags_ar") or [],

                "text_en": raw.get("text_en") or raw.get("description_en") or "",
                "text_ar": raw.get("text_ar") or raw.get("description_ar") or "",

                "img_to_text": raw.get("img_to_text") or [],
                "image_url": image_url,
                "image_urls": images,
                "image_paths": raw.get("image_paths") or [],
            }


            yield doc


# ---------------------------------------------------
# EMBEDDING + BULK
# ---------------------------------------------------
def iter_actions(embedder, docs, EMBED_DIM):
    for i, doc in enumerate(docs, 1):

        # build normalized fields
        image_text = extract_image_text(doc)
        en = build_search_text_en(doc)
        ar = build_search_text_ar(doc)
        combined = build_combined_text(doc, en, ar, image_text)

        doc["text_search_en"] = en
        doc["text_search_ar"] = ar
        doc["image_text"] = image_text
        doc["combined_text"] = combined

        # embedding
        emb_input = f"query: {combined}"
        vec = embedder.encode(emb_input, convert_to_numpy=True)

        if vec.shape[0] != EMBED_DIM:
            raise ValueError(
                f"Embedding dimension mismatch: got {vec.shape[0]}, expected {EMBED_DIM}"
            )

        doc["embedding"] = vec.tolist()

        # ID FIX — ensure unique + propagate to _source
        _id = doc.get("id") or str(uuid.uuid4())
        doc["id"] = _id  # <<< BUNU EKLEDİK

        if i % 300 == 0:
            log_info(f"Processed {i} docs...")

        yield {
            "_index": OPENSEARCH_INDEX,
            "_id": _id,
            "_source": doc,
        }

# ---------------------------------------------------
# VERIFY
# ---------------------------------------------------
def verify(client):
    client.indices.refresh(index=OPENSEARCH_INDEX)

    if not client.indices.exists(OPENSEARCH_INDEX):
        log_error("Index missing!")
        return

    count = client.count(index=OPENSEARCH_INDEX)["count"]
    log_info(f"Index count: {count}")

    if count == 0:
        log_warn("Index empty.")
        return

    res = client.search(index=OPENSEARCH_INDEX, body={"size": 3, "query": {"match_all": {}}})
    for idx, hit in enumerate(res["hits"]["hits"], 1):
        src = hit["_source"]
        print(GREEN + f"\n--- SAMPLE #{idx} ---" + RESET)
        print("ID:", src["id"])
        print("Brand:", src["brand"])
        print("Title:", src["title_en"])
        print("Group:", src["product_group"])
        print("Image:", src["image_url"])
        print("Image:", src["combined_text"])
        print("-------------------")


# ---------------------------------------------------
# MAIN
# ---------------------------------------------------
def main():
    log_info(f"Loading model: {EMBED_MODEL_NAME}")
    embedder = SentenceTransformer(EMBED_MODEL_NAME, device=device)

    # AUTO DETECT DIM
    EMBED_DIM = embedder.get_sentence_embedding_dimension()
    log_success(f"Detected embedding dimension: {EMBED_DIM}")

    client = OpenSearch(
        hosts=[OPENSEARCH_URL],
        http_auth=("admin", OPENSEARCH_PASSWORD),   # ALWAYS REQUIRED
        use_ssl=OPENSEARCH_URL.startswith("https"),
        verify_certs=False,
        ssl_show_warn=False,
        timeout=60,
        max_retries=5,
        retry_on_timeout=True,
    )

    # CREATE INDEX IF NOT EXISTS
    if not client.indices.exists(OPENSEARCH_INDEX):
        log_warn("Index does not exist. Creating...")
        client.indices.create(
            index=OPENSEARCH_INDEX,
            body={
                "settings": {
                    "index": {
                        "knn": True,
                        "knn.algo_param.ef_search": 512
                    }
                },
                "mappings": {
                    "properties": {
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": EMBED_DIM,
                            "method": {
                                "name": "hnsw",
                                "space_type": "l2",
                                "engine": "lucene"
                            }
                        }
                    }
                }
            }
        )
        log_success("Index created.")

    docs = list(iter_raw_documents())
    log_success(f"Loaded raw docs: {len(docs)}")

    docs = dedupe_docs(docs)

    log_info("Indexing to OpenSearch...")
    success, errors = helpers.bulk(client, iter_actions(embedder, docs, EMBED_DIM))
    log_success(f"Indexed: {success}")
    if errors:
        log_error(errors)

    verify(client)


if __name__ == "__main__":
    main()
