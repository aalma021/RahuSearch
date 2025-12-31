"""
FINAL PRODUCTION PIPELINE
JSONL → normalize → image_to_text flatten → EN/AR search fields →
combined_text → dedupe → embedding (OpenAI-compatible) → Weaviate bulk upload

IMPORTANT:
- Weaviate property adı "id" OLAMAZ (reserved). Bu yüzden:
  - App'in beklediği eski OpenSearch field "id" = Weaviate'ta "external_id" olarak saklanır.
  - Weaviate object UUID ise ayrı: uuid=to_weaviate_uuid(external_id)
- App tarafını değiştirmemek için: backend response'ta external_id -> id map edilir (query kısmında).
"""

import os
import json
import uuid
import uuid as uuid_pkg
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from dotenv import load_dotenv
import numpy as np
from openai import OpenAI

import weaviate
from weaviate.classes.config import Configure, DataType

# ---------------------------------------------------
# BASE DIR & ENV
# ---------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

load_dotenv()

# ---------------------------------------------------
# LOGGING (AYNEN)
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
# CONFIG (SADECE DB DEĞİŞTİ)
# ---------------------------------------------------
DATA_ROOT = Path((os.getenv("DATA_ROOT") or "").strip().strip('"').strip("'"))

WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
WEAVIATE_CLASS = os.getenv("WEAVIATE_CLASS", "products")

# OpenAI-compatible embedding (AYNEN)
EMBED_BASE_URL = os.getenv("EMBED_BASE_URL")
EMBED_API_KEY = os.getenv("EMBED_API_KEY", "EMPTY")
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL")

RECREATE_INDEX = (os.getenv("RECREATE_INDEX", "false").lower() == "true")

if not DATA_ROOT.exists():
    raise ValueError(f"DATA_ROOT not found: {DATA_ROOT}")

if not EMBED_MODEL_NAME:
    raise ValueError("EMBED_MODEL is required in .env.local")

if not EMBED_BASE_URL:
    raise ValueError("EMBED_BASE_URL is required in .env.local")

log_info(f"Weaviate: {WEAVIATE_URL} | Class: {WEAVIATE_CLASS}")
log_info(f"RECREATE_INDEX={RECREATE_INDEX}")
log_info(f"Embedding provider: OpenAI-compatible | base={EMBED_BASE_URL} | model={EMBED_MODEL_NAME}")

# ---------------------------------------------------
# EMBEDDING FIELD SELECTION (OPTIONAL)
# ---------------------------------------------------
EMBED_FIELDS = [
    f.strip()
    for f in os.getenv("EMBED_FIELDS", "").split(",")
    if f.strip()
]

if EMBED_FIELDS:
    log_info(f"Embedding fields (from env): {EMBED_FIELDS}")
else:
    log_info("EMBED_FIELDS not set → using combined_text")

# ---------------------------------------------------
# EMBEDDING (AYNEN)
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
        if not texts:
            return []

        res = self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        vectors = [d.embedding for d in res.data]

        if self._dim is None and vectors:
            self._dim = len(vectors[0])

        return vectors

    def dim(self) -> int:
        if self._dim is None:
            raise RuntimeError("Embedding dim unknown. Call embed() first.")
        return self._dim

# ---------------------------------------------------
# UUID HELPERS (WEAVIATE ZORUNLU)
# ---------------------------------------------------
def to_weaviate_uuid(value: str) -> str:
    """
    Deterministic UUID:
    SAME input -> SAME UUID
    """
    return str(uuid_pkg.uuid5(uuid_pkg.NAMESPACE_URL, value))

# ---------------------------------------------------
# BASIC HELPERS (OPENSEARCH'TEKİ İLE AYNI)
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
        doc.get("text_search"),
    ]
    parts.extend(doc.get("tags_en") or [])
    return dedup_words(" ".join(str(p) for p in parts if p))

def build_search_text_ar(doc: Dict[str, Any]) -> str:
    parts = [
        doc.get("title_ar"),
        doc.get("category_ar"),
        doc.get("text_ar"),
        doc.get("text_search_ar"),
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

def build_embedding_text(doc: Dict[str, Any]) -> str:
    """
    If EMBED_FIELDS is set:
      - Only those fields are used for embedding
    Else:
      - Fallback to combined_text (default behavior)
    """
    if not EMBED_FIELDS:
        return doc.get("combined_text", "")

    parts = []
    for field in EMBED_FIELDS:
        val = doc.get(field)
        if not val:
            continue

        if isinstance(val, list):
            parts.extend(str(x) for x in val if x)
        else:
            parts.append(str(val))

    return dedup_words(" ".join(parts))


# ---------------------------------------------------
# DEDUP KEYS (AYNI)
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
# RAW FILES (OPENSEARCH NORMALIZE İLE AYNI)
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
                # NOTE: OpenSearch'teki "id" (app field) burada da korunuyor ama
                # Weaviate property olarak "id" yazmayacağız; aşağıda external_id'ye map edeceğiz.
                "id": str(raw.get("id")) if raw.get("id") is not None else None,

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
# ITER ACTIONS (WEAVIATE UUID + COLUMN PARITY)
# ---------------------------------------------------
def iter_actions(embedding: GatewayEmbedding, docs: List[Dict[str, Any]], embed_dim: int):
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
        # embedding (configurable via EMBED_FIELDS)
        embed_text = build_embedding_text(doc)
        emb_input = f"query: {embed_text}"

        vec = embedding.embed([emb_input])[0]

        arr = np.array(vec, dtype=np.float32)
        # İstersen normalize kapat; açık hali genelde daha stabil olur.
        norm = float(np.linalg.norm(arr))
        if norm > 0:
            arr = arr / norm
        vec = arr.tolist()

        if len(vec) != embed_dim:
            raise ValueError(f"Embedding dimension mismatch: got {len(vec)}, expected {embed_dim}")

        # App parity için "embedding" property de yazıyoruz (ayrıca vector olarak da gönderiyoruz)
        doc["embedding"] = vec

        # ---- ID handling ----
        # OpenSearch'teki "id" alanını mutlaka doldur (fallback uuid)
        _id = doc.get("id") or str(uuid.uuid4())
        doc["id"] = _id

        # Weaviate property reserved "id" olamaz -> external_id kullan
        doc["external_id"] = _id

        # Weaviate object uuid (deterministic)
        doc["_weaviate_uuid"] = to_weaviate_uuid(_id)

        # Weaviate OBJECT/ARRAY uyumluluğu: img_to_text'ı JSON string sakla (kolon adı aynı)
        doc["img_to_text"] = json.dumps(doc.get("img_to_text") or [], ensure_ascii=False)

        if i % 300 == 0:
            log_info(f"Processed {i} docs...")

        yield doc

# ---------------------------------------------------
# WEAVIATE SCHEMA (OPENSEARCH COLUMNLARI = PROPERTIES)
# ---------------------------------------------------
def ensure_schema(client, embed_dim: int):
    existing = set(client.collections.list_all())

    if WEAVIATE_CLASS in existing and RECREATE_INDEX:
        log_warn("Deleting existing class...")
        client.collections.delete(WEAVIATE_CLASS)
        existing.discard(WEAVIATE_CLASS)

    if WEAVIATE_CLASS not in existing:
        log_warn("Creating class with OpenSearch-parity columns (id -> external_id)...")

        client.collections.create(
            name=WEAVIATE_CLASS,
            vector_config=Configure.Vectors.self_provided(),
            properties=[
                # identity / routing
                {"name": "external_id", "data_type": DataType.TEXT},  # <-- id yerine
                {"name": "store", "data_type": DataType.TEXT},
                {"name": "product_group", "data_type": DataType.TEXT},
                {"name": "url", "data_type": DataType.TEXT},
                {"name": "brand", "data_type": DataType.TEXT},

                # price
                {"name": "price_final", "data_type": DataType.NUMBER},
                {"name": "currency", "data_type": DataType.TEXT},

                # titles / categories
                {"name": "title_en", "data_type": DataType.TEXT},
                {"name": "title_ar", "data_type": DataType.TEXT},
                {"name": "category_en", "data_type": DataType.TEXT},
                {"name": "category_ar", "data_type": DataType.TEXT},

                # tags / text
                {"name": "tags_en", "data_type": DataType.TEXT_ARRAY},
                {"name": "tags_ar", "data_type": DataType.TEXT_ARRAY},
                {"name": "text_en", "data_type": DataType.TEXT},
                {"name": "text_ar", "data_type": DataType.TEXT},

                # images
                {"name": "image_url", "data_type": DataType.TEXT},
                {"name": "image_urls", "data_type": DataType.TEXT_ARRAY},
                {"name": "image_paths", "data_type": DataType.TEXT_ARRAY},

                # img2text (kolon adı aynı; JSON string)
                {"name": "img_to_text", "data_type": DataType.TEXT},

                # computed/search fields
                {"name": "text_search_en", "data_type": DataType.TEXT},
                {"name": "text_search_ar", "data_type": DataType.TEXT},
                {"name": "image_text", "data_type": DataType.TEXT},
                {"name": "combined_text", "data_type": DataType.TEXT},

                # embedding kolon parity (vector ayrı ama app "embedding" bekliyorsa burada da dursun)
                {"name": "embedding", "data_type": DataType.NUMBER_ARRAY},
            ],
        )
        log_success("Class created.")

# ---------------------------------------------------
# VERIFY
# ---------------------------------------------------
def verify(client, embed_dim: int):
    col = client.collections.get(WEAVIATE_CLASS)
    res = col.query.fetch_objects(limit=3, include_vector=True)

    log_info(f"Sample count: {len(res.objects)}")

    for i, obj in enumerate(res.objects, 1):
        if isinstance(obj.vector, dict):
            emb = obj.vector.get("default", [])
        else:
            emb = obj.vector or []

        norm = float(np.linalg.norm(np.array(emb))) if emb else -1.0

        p = obj.properties or {}

        print(GREEN + f"\n--- SAMPLE #{i} ---" + RESET)
        print("external_id (app.id):", p.get("external_id"))
        print("store:", p.get("store"))
        print("brand:", p.get("brand"))
        print("title_en:", (p.get("title_en") or "")[:80])
        print("product_group:", p.get("product_group"))
        print("image_url:", p.get("image_url"))
        print("combined_text_len:", len(p.get("combined_text") or ""))
        print("vector_dim:", len(emb), "| expected:", embed_dim)
        print("vector_norm:", norm)

        prop_emb = p.get("embedding") or []
        print("property_embedding_dim:", len(prop_emb))

# ---------------------------------------------------
# MAIN
# ---------------------------------------------------
def main():
    embedding = GatewayEmbedding()
    embedding.embed(["dim_probe"])
    embed_dim = embedding.dim()
    log_success(f"Detected embedding dimension: {embed_dim}")

    _u = WEAVIATE_URL.replace("http://", "").replace("https://", "")
    host = _u.split(":")[0]
    port = int(_u.split(":")[1]) if ":" in _u else 8080

    client = weaviate.connect_to_local(host=host, port=port, grpc_port=50051)

    try:
        ensure_schema(client, embed_dim)

        docs = list(iter_raw_documents())
        log_success(f"Loaded raw docs: {len(docs)}")

        docs = dedupe_docs(docs)

        log_info("Indexing to Weaviate...")
        col = client.collections.get(WEAVIATE_CLASS)

        # ✅ OpenSearch kolon parity whitelist (id -> external_id)
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
            "text_search_en",
            "text_search_ar",
            "image_text",
            "combined_text",
            "embedding",
        }

        with col.batch.dynamic() as batch:
            for doc in iter_actions(embedding, docs, embed_dim):
                batch.add_object(
                    properties={k: doc.get(k) for k in allowed_props},
                    vector=doc["embedding"],           # vector store
                    uuid=doc["_weaviate_uuid"]         # deterministic uuid
                )

        verify(client, embed_dim)

    finally:
        # ✅ leak olmasın diye MUTLAKA
        client.close()

if __name__ == "__main__":
    main()
