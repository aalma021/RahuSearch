from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes.search_router import router as search_router
from app.utils.logger import logger
from app.config.settings import DATA_ROOT

app = FastAPI(
    title="AI Semantic Search API",
    version="1.0.0",
)

# -----------------------------------------------------
# 🔥 Static Files for Image Serving
# -----------------------------------------------------
# Exposes DATA_ROOT as /images → allowing the frontend
# to load images through a valid public URL instead
# of local filesystem paths.
app.mount("/images", StaticFiles(directory=DATA_ROOT), name="images")

# -----------------------------------------------------
# 🔥 CORS Middleware
# -----------------------------------------------------
# Allows requests from any frontend client. Adjust
# `allow_origins` for production environments.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("[API] FastAPI startup event fired")

# -----------------------------------------------------
# 🔥 API Routers
# -----------------------------------------------------
# Registers the search router where the semantic
# search endpoint is implemented.
app.include_router(search_router)
