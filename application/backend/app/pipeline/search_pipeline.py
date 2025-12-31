# app/pipelines/search_pipeline.py
from app.preprocessing.text_processor import TextProcessor
from app.openrouter.image_processor import ImageProcessor
from app.preprocessing.input_router import InputRouter
from app.processors.search_processor import SearchProcessor
from app.db.weaviate_backend import WeaviateBackend
from app.utils.path_utils import build_full_image_paths
from app.utils.logger import logger


class SearchPipeline:
    """
    Pipeline = orchestration only
    Business logic lives in SearchProcessor
    DB logic lives in backend
    """

    def __init__(self):
        # -----------------------------
        # PREPROCESSORS
        # -----------------------------
        self.text_proc = TextProcessor()
        self.image_proc = ImageProcessor()
        self.router = InputRouter()

        # -----------------------------
        # DB BACKEND (TEK SATIR)
        # -----------------------------
        backend = WeaviateBackend()

        # -----------------------------
        # SEARCH INTELLIGENCE
        # -----------------------------
        self.searcher = SearchProcessor(backend)

    def run(
        self,
        text=None,
        image_bytes=None,
        mode="hybrid",
        k=25,
        alpha=0.5,
        reranker=True,
        reranker_threshold=0.0,
        store=None
    ):
        # ------------------------------------------------
        # INPUT
        # ------------------------------------------------
        clean_text = self.text_proc.process(text) if text else ""
        image_text = self.image_proc.process(image_bytes) if image_bytes else ""

        query = self.router.merge(clean_text, image_text)

        if not query:
            return {"error": "Empty query"}

        logger.info(
            "[Pipeline] mode=%s k=%s alpha=%s reranker=%s store=%s",
            mode, k, alpha, reranker, store
        )

        # ------------------------------------------------
        # SEARCH (MODE SWITCH HERE ✔)
        # ------------------------------------------------
        if mode == "keyword":
            hits = self.searcher.keyword(query, k, store)

        elif mode == "vector":
            hits = self.searcher.vector(query, k, store)

        elif mode == "hybrid":
            hits = self.searcher.hybrid(query, k, alpha, store)

        else:
            return {"error": f"Invalid mode={mode}"}

        # ------------------------------------------------
        # RERANKER
        # ------------------------------------------------
        if reranker:
            from app.ranking.reranker_processor import RerankerProcessor

            rer = RerankerProcessor()
            hits = rer.rerank(query, hits)

            if reranker_threshold:
                hits = [
                    h for h in hits
                    if float(h.get("rerank_score", 0.0)) >= reranker_threshold
                ]

        # ------------------------------------------------
        # RESPONSE
        # ------------------------------------------------
        results = []
        logger.info("hits are: %s", hits)
        for h in hits[:k]:
            src = h  # backend normalize edilmiş dict

            results.append({
                # ✅ SADECE BU SATIR GÜNCELLENDİ
                # Weaviate: external_id
                # OpenSearch legacy: id
                "id": src.get("id") or src.get("external_id"),

                "title_en": src.get("title_en"),
                "title_ar": src.get("title_ar"),
                "brand": src.get("brand"),
                "url": src.get("url"),
                "price": src.get("price_final"),
                "currency": src.get("currency"),
                "product_group": src.get("product_group"),
                "image_paths": build_full_image_paths(
                    src.get("store"),
                    src.get("image_paths")
                ),
                "store": src.get("store"),
                "score": float(src.get("final_score", 0.0)),
                "rerank_score": float(src.get("rerank_score", 0.0)),
            })

        return {
            "query": query,
            "results": results
        }
