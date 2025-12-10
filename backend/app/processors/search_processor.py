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
    def keyword(self, query, k, store=None):
        logger.info(f"[SearchProcessor] Keyword search → k={k}")

        body = {
            "size": k,
            "query": {"match": {"combined_text": query}}
        }

        if store:
            body["query"] = {
                "bool": {
                    "must": body["query"],
                    "filter": {"term": {"store": store.lower()}}
                }
            }

        start = time.perf_counter()
        res = self.client.search(index=self.index, body=body)
        elapsed = time.perf_counter() - start

        logger.info(f"[SearchProcessor] Keyword duration: {elapsed:.4f} sec")
        return res["hits"]["hits"]

    # --------------------------------------------------
    # VECTOR SEARCH
    # --------------------------------------------------
    def vector(self, query, k, store=None):
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

        if store:
            body["query"] = {
                "bool": {
                    "must": body["query"],
                    "filter": {"term": {"store": store.lower()}}
                }
            }

        start = time.perf_counter()
        res = self.client.search(index=self.index, body=body)
        elapsed = time.perf_counter() - start

        logger.info(f"[SearchProcessor] Vector duration: {elapsed:.4f} sec")
        return res["hits"]["hits"]

    # --------------------------------------------------
    # HYBRID (RAW)
    # --------------------------------------------------
    def get_hybrid_raw(self, query, k, alpha, store=None):
        logger.info(f"[SearchProcessor] Hybrid(raw) → k={k}, alpha={alpha}, store={store}")

        emb = self.embed_proc.model.encode(
            "query: " + query,
            convert_to_numpy=True
        )

        pipeline = f"hybrid-a{alpha}"
        self._update_pipeline(alpha, pipeline)
        params = {"search_pipeline": pipeline}

        query_body = {
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

        body = {
            "size": k,
            "query": query_body
        }

        # post_filter applies AFTER scoring & ranking
        if store:
            body["post_filter"] = {
                "term": {"store": store.lower()}
            }

        start = time.perf_counter()
        res = self.client.search(index=self.index, body=body, params=params)
        elapsed = time.perf_counter() - start

        logger.info(f"[SearchProcessor] Hybrid(raw) duration: {elapsed:.4f} sec")
        return res["hits"]["hits"]

    # --------------------------------------------------
    # HYBRID FILTERED + RESTRICTED (TRUE USER EXPECTATION)
    # --------------------------------------------------
    def hybrid(self, query, k, alpha, store=None):
        logger.info(
            f"[SearchProcessor] Hybrid(filtered) → k={k}, alpha={alpha}, store={store}"
        )

        # Expand pool — ensure we find enough store-matching products
        expanded_k = max(k * 4, 200)
        raw_hits = self.get_hybrid_raw(query, expanded_k, alpha)

        if store:
            filtered = [
                x for x in raw_hits
                if x["_source"]["store"].lower() == store.lower()
            ]
        else:
            filtered = raw_hits

        # Final slice (top-K)
        return filtered[:k]

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
