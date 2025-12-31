import os
from openai import OpenAI
from app.embedding.base import BaseEmbedding

class GatewayEmbedding(BaseEmbedding):
    """
    Backend için TEK embedding implementasyonu.
    Provider bilmez.
    Sadece OpenAI-compatible embedding endpoint bilir.
    """

    def __init__(self):
        self.client = OpenAI(
            base_url=os.getenv("EMBED_BASE_URL"),
            api_key=os.getenv("EMBED_API_KEY", "EMPTY"),
        )

        self.model = os.getenv("EMBED_MODEL")
        if not self.model:
            raise RuntimeError("EMBED_MODEL env is required")

        self._dim = None

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        res = self.client.embeddings.create(
            model=self.model,
            input=texts
        )

        vectors = [d.embedding for d in res.data]

        # dim AUTO-DETECT (ilk çağrıda)
        if self._dim is None and vectors:
            self._dim = len(vectors[0])

        return vectors

    def dim(self) -> int:
        if self._dim is None:
            raise RuntimeError("Embedding dim unknown. Call embed() first.")
        return self._dim
