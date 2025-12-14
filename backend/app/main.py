import uvicorn
from app.api.api import app
from app.utils.logger import logger


def start():
    logger.info("[Main] Starting AI Semantic Search API via Uvicorn")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    start()
