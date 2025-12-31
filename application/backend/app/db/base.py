# app/db/base.py
from abc import ABC, abstractmethod


class SearchBackend(ABC):
    """
    DB backend interface.

    Responsibility:
    - Fetch candidate documents
    - NO scoring
    - NO embedding computation
    """

    @abstractmethod
    def get_candidates(
        self,
        query: str,
        k: int,
        store: str | None = None,
        *,
        with_vector: bool = False
    ) -> list[dict]:
        """
        BM25-based candidate retrieval.

        with_vector:
            If True, backend may attach stored vector
            under key: "embedding"
        """
        raise NotImplementedError

    # --------------------------------------------------
    # PURE VECTOR SEARCH (BM25 YOK)
    # --------------------------------------------------
    @abstractmethod
    def vector_search(
        self,
        vector: list[float],
        k: int,
        store: str | None = None
    ) -> list[dict]:
        """
        PURE vector search.

        - NO keyword
        - NO BM25
        - Vector similarity only
        """
        raise NotImplementedError
