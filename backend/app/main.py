# app/main.py
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes.search_router import router as search_router
from app.config.settings import DATA_ROOT
from app.utils.logger import logger

# -----------------------------------------------------
# FASTAPI APP
# -----------------------------------------------------
app = FastAPI(
    title="AI Semantic Search API",
    version="1.0.0",
)

# -----------------------------------------------------
# CORS (PINGGY + BROWSER UYUMLU)
# -----------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------
# STATIC FILES (/images)
# -----------------------------------------------------
app.mount("/images", StaticFiles(directory=DATA_ROOT), name="images")

# -----------------------------------------------------
# ROUTERS
# -----------------------------------------------------
app.include_router(search_router)

# -----------------------------------------------------
# STARTUP LOG
# -----------------------------------------------------
@app.on_event("startup")
async def startup_event():
    logger.info("[API] FastAPI startup event fired")

# -----------------------------------------------------
# ENTRYPOINT
# -----------------------------------------------------
def start():
    logger.info("[Main] Starting AI Semantic Search API via Uvicorn")

    uvicorn.run(
        app,                  # 🔥 STRING YOK, DİREKT APP
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True,
    )

if __name__ == "__main__":
    start()
