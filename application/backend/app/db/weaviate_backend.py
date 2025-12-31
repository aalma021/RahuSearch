# app/db/weaviate_backend.py
import weaviate
from weaviate.classes.query import Filter

from app.db.base import SearchBackend
from app.config.settings import WEAVIATE_URL, WEAVIATE_CLASS
from app.utils.logger import logger


class WeaviateBackend(SearchBackend):
    """
    Weaviate backend (v4 collections API).

    - get_candidates()  -> BM25
    - vector_search()   -> PURE vector (BM25 YOK)
    """

    def __init__(self):
        self._client = None
        self.class_name = WEAVIATE_CLASS

        logger.info(
            "[WeaviateBackend] Connected → %s (class=%s)",
            WEAVIATE_URL,
            WEAVIATE_CLASS
        )

    # --------------------------------------------------
    # CLIENT (Weaviate v4)
    # --------------------------------------------------
    @property
    def client(self):
        if self._client is None:
            _u = WEAVIATE_URL.replace("http://", "").replace("https://", "")
            host = _u.split(":")[0]
            port = int(_u.split(":")[1]) if ":" in _u else 8080

            self._client = weaviate.connect_to_local(
                host=host,
                port=port,
                grpc_port=50051
            )
        return self._client

    # --------------------------------------------------
    # BM25 CANDIDATES
    # --------------------------------------------------
    def get_candidates(
        self,
        query: str,
        k: int,
        store: str | None = None,
        *,
        with_vector: bool = False
    ) -> list[dict]:

        properties = [
            "external_id",
            "title_en",
            "title_ar",
            "brand",
            "url",
            "price_final",
            "currency",
            "product_group",
            "image_paths",
            "store",
            "combined_text",
        ]

        col = self.client.collections.get(self.class_name)

        filters = None
        if store:
            filters = Filter.by_property("store").equal(store)

        res = col.query.bm25(
            query=query,
            limit=k,
            filters=filters,
            return_properties=properties,
            return_metadata=["score"],
            include_vector=with_vector
        )

        if not res.objects:
            return []

        out: list[dict] = []

        for obj in res.objects:
            hit: dict = {}

            for key in properties:
                hit[key] = obj.properties.get(key)

            hit["id"] = hit.get("external_id")
            hit["_score"] = float(obj.metadata.score or 1.0)

            if with_vector:
                vec = obj.vector
                if isinstance(vec, dict):
                    vec = vec.get("default")
                hit["embedding"] = vec if isinstance(vec, list) else None

            out.append(hit)

        return out

    # --------------------------------------------------
    # PURE VECTOR SEARCH (BM25 YOK)
    # --------------------------------------------------
    def vector_search(
        self,
        vector: list[float],
        k: int,
        store: str | None = None
    ) -> list[dict]:

        properties = [
            "external_id",
            "title_en",
            "title_ar",
            "brand",
            "url",
            "price_final",
            "currency",
            "product_group",
            "image_paths",
            "store",
            "combined_text",
        ]

        col = self.client.collections.get(self.class_name)

        filters = None
        if store:
            filters = Filter.by_property("store").equal(store)

        res = col.query.near_vector(
            near_vector=vector,
            limit=k,
            filters=filters,
            return_properties=properties,
            return_metadata=["distance"]
        )

        if not res.objects:
            return []

        out: list[dict] = []

        for obj in res.objects:
            hit: dict = {}

            for key in properties:
                hit[key] = obj.properties.get(key)

            hit["id"] = hit.get("external_id")

            # cosine distance → similarity
            distance = float(obj.metadata.distance or 0.0)
            hit["final_score"] = 1.0 - distance

            out.append(hit)

        return out
