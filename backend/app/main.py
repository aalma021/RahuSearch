import uvicorn
from app.utils.logger import logger


def start():
    logger.info("[Main] Starting AI Semantic Search API via Uvicorn")

    uvicorn.run(
        "app.api.api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    start()
