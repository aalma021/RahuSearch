import torch
from sentence_transformers import SentenceTransformer
from app.utils.logger import logger


class EmbeddingProcessor:
    """
    Embedding-based vector search using any sentence-transformer model.
    Auto-detects embedding dimension from model.
    """

    def __init__(self, model_name: str):
        device = "cuda" if torch.cuda.is_available() else "cpu"

        logger.info("[Embedding] Loading model=%s device=%s", model_name, device)
        self.model = SentenceTransformer(model_name, device=device)
        logger.info("[Embedding] Model loaded successfully")

        # AUTO DETECT EMBEDDING DIMENSION
        self.dim = self.model.get_sentence_embedding_dimension()
        logger.info("[Embedding] Auto-detected embedding dimension: %s", self.dim)

    def search(self, client, index, query: str, top_k: int = 200):
        if not query:
            logger.warning("[Embedding] Empty query received. Skipping search.")
            return []

        logger.debug("[Embedding] Encoding query")
        emb = self.model.encode(query, convert_to_numpy=True)

        if len(emb) != self.dim:
            logger.error("[EMBED ERROR] Model returned dim=%s but expected %s",
                         len(emb), self.dim)
            return []

        logger.debug("[Embedding] Query encoded. Running k-NN vector search")

        # ✅ CORRECT OpenSearch k-NN FORMAT
        body = {
            "size": top_k,
            "query": {
                "knn": {
                    "embedding": {            # field name
                        "vector": emb.tolist(),  # correct key
                        "k": top_k
                    }
                }
            }
        }

        try:
            logger.debug("[Embedding] Sending k-NN search to OpenSearch")
            res = client.search(index=index, body=body)
            hits = res["hits"]["hits"]
            logger.info("[Embedding] Retrieved %s vector hits", len(hits))
            return hits

        except Exception as e:
            logger.error("[VECTOR SEARCH ERROR] %s", e)
            return []
