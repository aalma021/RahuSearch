import time
from app.utils.logger import logger
from app.embedding.embedding_processor import EmbeddingProcessor


class SearchProcessor:

    def __init__(self, client, index, model_name):
        self.client = client
        self.index = index

        # Load embedding model ONCE
        self.embed_proc = EmbeddingProcessor(model_name)

    # --------------------------------------------------
    # KEYWORD
    # --------------------------------------------------
    def keyword(self, query, k):
        logger.info(f"[SearchProcessor] Keyword search → k={k}")

        body = {
            "size": k,
            "query": {"match": {"combined_text": query}}
        }

        start = time.perf_counter()
        res = self.client.search(index=self.index, body=body)
        elapsed = time.perf_counter() - start

        logger.info(f"[SearchProcessor] Keyword duration: {elapsed:.4f} sec")

        return res["hits"]["hits"]

    # --------------------------------------------------
    # VECTOR SEARCH (pure embedding)
    # --------------------------------------------------
    def vector(self, query, k):
        logger.info(f"[SearchProcessor] Vector search → k={k}")

        emb = self.embed_proc.model.encode(
            "query: " + query,
            convert_to_numpy=True
        )

        body = {
            "size": k,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": emb.tolist(),
                        "k": k
                    }
                }
            }
        }

        start = time.perf_counter()
        res = self.client.search(index=self.index, body=body)
        elapsed = time.perf_counter() - start

        logger.info(f"[SearchProcessor] Vector duration: {elapsed:.4f} sec")

        return res["hits"]["hits"]

    # --------------------------------------------------
    # HYBRID SEARCH (BM25 + KNN)
    # --------------------------------------------------
    def hybrid(self, query, k, alpha):
        logger.info(f"[SearchProcessor] Hybrid search → k={k}, alpha={alpha}")

        emb = self.embed_proc.model.encode(
            "query: " + query,
            convert_to_numpy=True
        )

        pipeline = f"hybrid-a{alpha}"
        self._update_pipeline(alpha, pipeline)

        params = {"search_pipeline": pipeline}

        # native hybrid query
        body = {
            "size": k,
            "query": {
                "hybrid": {
                    "queries": [
                        {"match": {"combined_text": query}},
                        {
                            "knn": {
                                "embedding": {
                                    "vector": emb.tolist(),
                                    "k": k
                                }
                            }
                        }
                    ]
                }
            }
        }

        start = time.perf_counter()
        res = self.client.search(index=self.index, body=body, params=params)
        elapsed = time.perf_counter() - start

        logger.info(f"[SearchProcessor] Hybrid search duration: {elapsed:.4f} sec")

        return res["hits"]["hits"]

    # --------------------------------------------------
    # CREATE/UPDATE HYBRID PIPELINE
    # --------------------------------------------------
    def _update_pipeline(self, alpha, name):
        body = {
            "phase_results_processors": [
                {
                    "normalization-processor": {
                        "normalization": {"technique": "min_max"},
                        "combination": {
                            "technique": "arithmetic_mean",
                            "parameters": {"weights": [1 - alpha, alpha]}
                        }
                    }
                }
            ]
        }

        start = time.perf_counter()
        self.client.transport.perform_request(
            method="PUT",
            url=f"/_search/pipeline/{name}",
            body=body,
        )
        elapsed = time.perf_counter() - start

        logger.info(f"[SearchProcessor] Pipeline PUT duration: {elapsed:.4f} sec")
