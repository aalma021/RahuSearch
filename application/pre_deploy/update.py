"""
UPDATE PIPELINE (SAFE)

- Existing Weaviate index üzerine veri ekler / günceller
- Schema / index creation YOK
- Deterministic UUID (external_id -> uuid5)
- OpenSearch parity korunur
"""

import os
import json
import uuid as uuid_pkg
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
import weaviate
from weaviate.exceptions import UnexpectedStatusCodeError

# ---------------------------------------------------
# ENV
# ---------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)
load_dotenv()

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
WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_CLASS = os.getenv("WEAVIATE_CLASS")

UPDATE_MODE = os.getenv("UPDATE_MODE", "true").lower() == "true"
SKIP_EXISTING = os.getenv("SKIP_EXISTING", "false").lower() == "true"

EMBED_BASE_URL = os.getenv("EMBED_BASE_URL")
EMBED_API_KEY = os.getenv("EMBED_API_KEY", "EMPTY")
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL")

EMBED_FIELDS = [
    f.strip() for f in os.getenv("EMBED_FIELDS", "").split(",") if f.strip()
]

if not DATA_ROOT.exists():
    raise ValueError(f"DATA_ROOT not found: {DATA_ROOT}")

log_info(f"UPDATE_MODE={UPDATE_MODE} | SKIP_EXISTING={SKIP_EXISTING}")
log_info(f"Weaviate={WEAVIATE_URL} | Class={WEAVIATE_CLASS}")

# ---------------------------------------------------
# EMBEDDING
# ---------------------------------------------------
class GatewayEmbedding:
    def __init__(self):
        self.client = OpenAI(
            base_url=EMBED_BASE_URL,
            api_key=EMBED_API_KEY,
        )
        self.model = EMBED_MODEL_NAME
        self._dim = None

    def embed(self, texts: List[str]) -> List[List[float]]:
        res = self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        vecs = [d.embedding for d in res.data]
        if self._dim is None:
            self._dim = len(vecs[0])
        return vecs

# ---------------------------------------------------
# UUID (DETERMINISTIC)
# ---------------------------------------------------
def to_weaviate_uuid(value: str) -> str:
    return str(uuid_pkg.uuid5(uuid_pkg.NAMESPACE_URL, value))

# ---------------------------------------------------
# HELPERS
# ---------------------------------------------------
def dedup_words(text: str) -> str:
    if not text:
        return ""
    seen, out = set(), []
    for w in text.split():
        k = w.lower()
        if k not in seen:
            out.append(w)
            seen.add(k)
    return " ".join(out)

def build_embedding_text(doc: Dict[str, Any]) -> str:
    if not EMBED_FIELDS:
        return doc.get("combined_text", "")
    parts = []
    for f in EMBED_FIELDS:
        v = doc.get(f)
        if isinstance(v, list):
            parts.extend(str(x) for x in v if x)
        elif v:
            parts.append(str(v))
    return dedup_words(" ".join(parts))

# ---------------------------------------------------
# RAW DOCS
# ---------------------------------------------------
def iter_raw_docs():
    for path in DATA_ROOT.rglob("*.jsonl"):
        log_info(f"Reading {path}")
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                raw = json.loads(line)

                images = raw.get("image_urls") or []

                yield {
                    "store": raw.get("store"),
                    "product_group": path.parent.name,
                    "url": raw.get("url") or raw.get("url_en"),
                    "brand": raw.get("brand"),
                    "price_final": raw.get("price_sar") or raw.get("price_aed"),
                    "currency": "SAR" if raw.get("price_sar") else "AED",
                    "title_en": raw.get("title_en"),
                    "title_ar": raw.get("title_ar"),
                    "category_en": raw.get("category_en"),
                    "category_ar": raw.get("category_ar"),
                    "tags_en": raw.get("tags_en") or [],
                    "tags_ar": raw.get("tags_ar") or [],
                    "text_en": raw.get("text_en") or "",
                    "text_ar": raw.get("text_ar") or "",
                    "combined_text": raw.get("combined_text") or "",
                    "image_url": images[0] if images else None,
                    "image_urls": images,
                    "image_paths": raw.get("image_paths") or [],
                    "img_to_text": json.dumps(raw.get("img_to_text") or [], ensure_ascii=False),
                }

# ---------------------------------------------------
# MAIN
# ---------------------------------------------------
def main():
    embedding = GatewayEmbedding()
    embedding.embed(["dim_probe"])

    host = WEAVIATE_URL.replace("http://", "").split(":")[0]
    port = int(WEAVIATE_URL.split(":")[-1])

    client = weaviate.connect_to_local(host=host, port=port, grpc_port=50051)

    inserted = updated = skipped = 0

    try:
        col = client.collections.get(WEAVIATE_CLASS)

        allowed_props = {
            "external_id",
            "store",
            "product_group",
            "url",
            "brand",
            "price_final",
            "currency",
            "title_en",
            "title_ar",
            "category_en",
            "category_ar",
            "tags_en",
            "tags_ar",
            "text_en",
            "text_ar",
            "img_to_text",
            "image_url",
            "image_urls",
            "image_paths",
            "combined_text",
            "embedding",
        }

        for doc in iter_raw_docs():

            url = doc.get("url")
            if not url:
                skipped += 1
                continue

            external_id = url.strip()
            uuid_w = to_weaviate_uuid(external_id)
            doc["external_id"] = external_id

            text = build_embedding_text(doc)
            vec = embedding.embed([f"query: {text}"])[0]

            arr = np.array(vec, dtype=np.float32)
            n = np.linalg.norm(arr)
            if n > 0:
                arr = arr / n
            doc["embedding"] = arr.tolist()

            props = {k: doc.get(k) for k in allowed_props}

            # ---------------------------------------------------
            # 🔥 FINAL SAFE UPSERT
            # ---------------------------------------------------
            if UPDATE_MODE:
                try:
                    col.data.update(
                        uuid=uuid_w,
                        properties=props,
                        vector=doc["embedding"],
                    )
                    if SKIP_EXISTING:
                        skipped += 1
                    else:
                        updated += 1
                    continue

                except UnexpectedStatusCodeError as e:
                    msg = str(e)
                    if "404" not in msg:
                        raise e
                    # else → insert fallback

            # ---- INSERT PATH ----
            try:
                col.data.insert(
                    uuid=uuid_w,
                    properties=props,
                    vector=doc["embedding"],
                )
                inserted += 1

            except UnexpectedStatusCodeError as e:
                # 422 → already exists → SKIP
                skipped += 1

    finally:
        client.close()

    log_success(f"Inserted: {inserted}")
    log_success(f"Updated: {updated}")
    log_warn(f"Skipped: {skipped}")

if __name__ == "__main__":
    main()
