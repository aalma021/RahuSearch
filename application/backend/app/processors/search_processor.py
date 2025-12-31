# app/processors/search_processor.py
import time
import numpy as np

from app.utils.logger import logger
from app.embedding.factory import get_embedding
from app.utils.vector_utils import cosine
from app.db.base import SearchBackend


class SearchProcessor:
    """
    SearchProcessor = ALL SEARCH INTELLIGENCE

    - Embeddings
    - Cosine similarity
    - Alpha fusion
    - Vector-only search (PURE VECTOR)
    - Hybrid search (BM25 + vector)

    DB = dumb candidate provider
    """

    def __init__(self, backend: SearchBackend):
        self.backend = backend
        self.embedding = get_embedding()

        logger.info(
            "[SearchProcessor] Initialized with backend=%s",
            backend.__class__.__name__
        )

    # --------------------------------------------------
    # KEYWORD (BM25)
    # --------------------------------------------------
    def keyword(self, query: str, k: int, store: str | None = None):
        logger.info("[SearchProcessor] keyword → k=%s store=%s", k, store)

        start = time.perf_counter()
        hits = self.backend.get_candidates(query, k, store)
        logger.info(
            "[SearchProcessor] keyword took %.4fs",
            time.perf_counter() - start
        )

        return hits

    # --------------------------------------------------
    # VECTOR (PURE VECTOR SEARCH - BM25 YOK)
    # --------------------------------------------------
    def vector(self, query: str, k: int, store: str | None = None):
        logger.info("[SearchProcessor] vector → k=%s store=%s", k, store)

        # 1️⃣ query embedding
        q_vec = self.embedding.embed([query])[0]
        q_vec = np.array(q_vec, dtype=np.float32)

        # normalize
        norm = np.linalg.norm(q_vec)
        if norm > 0:
            q_vec = (q_vec / norm).tolist()
        else:
            q_vec = q_vec.tolist()

        logger.info("query embedding dim=%s", len(q_vec))

        # 2️⃣ PURE vector search (DB tarafı)
        start = time.perf_counter()
        hits = self.backend.vector_search(
            vector=q_vec,
            k=k,
            store=store
        )
        logger.info(
            "[SearchProcessor] vector search took %.4fs",
            time.perf_counter() - start
        )

        return hits

    # --------------------------------------------------
    # HYBRID (BM25 + cosine fusion)
    # --------------------------------------------------
    def hybrid(
        self,
        query: str,
        k: int,
        alpha: float,
        store: str | None = None
    ):
        logger.info(
            "[SearchProcessor] hybrid → k=%s alpha=%s store=%s",
            k, alpha, store
        )

        # 1️⃣ BM25 candidate pool
        hits = self.backend.get_candidates(
            query,
            k * 5,
            store,
            with_vector=True
        )
        if not hits:
            return []

        # 2️⃣ query embedding + normalize
        q_vec = self.embedding.embed([query])[0]
        q_vec = np.array(q_vec, dtype=np.float32)
        norm = np.linalg.norm(q_vec)
        if norm > 0:
            q_vec = (q_vec / norm).tolist()

        # 3️⃣ alpha fusion
        for h in hits:
            bm25 = float(h.get("_score", 1.0))
            bm25 = min(bm25, 5.0) / 5.0  # scale fix

            doc_vec = h.get("embedding")
            vector_score = cosine(q_vec, doc_vec) if doc_vec else 0.0

            h["final_score"] = alpha * vector_score + (1 - alpha) * bm25

        hits.sort(key=lambda x: x["final_score"], reverse=True)
        return hits[:k]
