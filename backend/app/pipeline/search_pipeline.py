from app.db.opensearch import get_client
from app.preprocessing.text_processor import TextProcessor
from app.preprocessing.image_processor import ImageProcessor
from app.preprocessing.input_router import InputRouter
from app.processors.search_processor import SearchProcessor
from app.utils.path_utils import build_full_image_paths
from app.config.settings import OPENSEARCH_INDEX, EMBED_MODEL
from app.utils.logger import logger


class SearchPipeline:
    def __init__(self):
        self.client = get_client()

        self.text_proc = TextProcessor()
        self.image_proc = ImageProcessor()
        self.router = InputRouter()

        self.searcher = SearchProcessor(
            client=self.client,
            index=OPENSEARCH_INDEX,
            model_name=EMBED_MODEL
        )

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
        clean = self.text_proc.process(text) if text else ""
        img_txt = self.image_proc.process(image_bytes) if image_bytes else ""

        query = self.router.merge(clean, img_txt)

        if not query:
            return {"error": "Empty query"}
        logger.warning(
            f"[DEBUG] mode={mode}, k={k}, alpha={alpha}, reranker={reranker}, "
            f"threshold={reranker_threshold}, query={query}, store={store}"
        )

        # ------------------------------------------------
        # RETRIEVAL MODES
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
        # RERANKING
        # ------------------------------------------------
        if reranker:
            from app.ranking.reranker_processor import RerankerProcessor
            self.reranker = RerankerProcessor()

            hits = self.reranker.rerank(query, hits)

            if reranker_threshold:
                hits = [
                    h for h in hits
                    if float(h.get("rerank_score", 0)) >= reranker_threshold
                ]

        # ------------------------------------------------
        # BUILD RESPONSE DTO
        # ------------------------------------------------
        results = []
        for h in hits[:k]:
            src = h["_source"]

        results = []
        for h in hits[:k]:
            src = h["_source"]

            results.append({
                "id": src.get("id"),
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

                "store": src.get("store"),  # eklenmesi mantıklı

                "score": float(h.get("_score", 0.0)),
                "rerank_score": float(h.get("rerank_score", 0.0))
            })

        return {
            "query": query,
            "results": results
        }
