from FlagEmbedding import FlagReranker
from app.utils.logger import logger
import torch
import time

device = "cuda" if torch.cuda.is_available() else "cpu"

class RerankerProcessor:
    """
    Efficient multilingual reranker using FlagEmbedding.
    Model: BAAI/bge-reranker-v2-m3
    """

    def __init__(self):
        logger.info("[Reranker] Loading FlagEmbedding model: BAAI/bge-reranker-v2-m3")
        logger.info(f"[Reranker] Device selected: {device.upper()}")

        self.model = FlagReranker(
            "BAAI/bge-reranker-v2-m3",
            use_fp16=True,
            device=device
        )

        logger.info("[Reranker] Model loaded successfully")

    def rerank(self, query, docs):
        logger.debug(f"[Reranker] Starting rerank for {len(docs)} documents")

        pairs = []
        for d in docs:
            src = d.get("_source", {})
            text = src.get("combined_text") \
                or src.get("title_en") \
                or ""
            pairs.append([query, text])

        logger.debug("[Reranker] Computing cross-encoder relevance scores...")

        start = time.perf_counter()
        scores = self.model.compute_score(pairs)
        elapsed = time.perf_counter() - start

        logger.info(f"[Reranker] Scoring duration: {elapsed:.4f} sec using {device.upper()}")

        scores = [float(s) for s in scores]

        for d, s in zip(docs, scores):
            d["rerank_score"] = s

        docs.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)

        logger.info(f"[Reranker] Reranking completed → {len(docs)} docs sorted")

        return docs
