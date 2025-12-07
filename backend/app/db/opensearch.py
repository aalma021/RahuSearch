from opensearchpy import OpenSearch
from app.config.settings import (
    OPENSEARCH_URL,
    OPENSEARCH_PASSWORD,
)
from app.utils.logger import logger


_client = None


def get_client():
    global _client
    if _client is not None:
        return _client

    logger.info("[OpenSearch] Initializing client")

    _client = OpenSearch(
        hosts=[OPENSEARCH_URL],
        http_auth=("admin", OPENSEARCH_PASSWORD),
        verify_certs=False,
        ssl_show_warn=False,
        timeout=60,
        max_retries=5,
        retry_on_timeout=True,
    )

    logger.info("[OpenSearch] Client initialized")
    return _client
