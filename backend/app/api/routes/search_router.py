# app/api/routes/search_router.py
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, Response
from app.pipeline.search_pipeline import SearchPipeline

# -----------------------------------------------------
# ROUTER
# -----------------------------------------------------
router = APIRouter()
pipeline = SearchPipeline()

# -----------------------------------------------------
# CORS PREFLIGHT (CRITICAL)
# -----------------------------------------------------
@router.options("/search")
async def search_options(response: Response):
    """
    Explicit OPTIONS handler for CORS preflight.
    Required for multipart/form-data + proxy (Pinggy).
    """
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return {}

# -----------------------------------------------------
# SEARCH ENDPOINT
# -----------------------------------------------------
@router.post("/search")
async def search(
    text: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),

    mode: str = Form("hybrid"),
    k: int = Form(25),
    alpha: float = Form(0.5),
    reranker: bool = Form(True),
    reranker_score: float = Form(0.0),

    store: Optional[str] = Form(None),
):
    """
    Semantic Search API

    Parameters:
    ----------
    text : str
        Query string (optional if uploading image)
    image : file
        Optional image input (OCR → semantic text)
    mode : keyword | vector | hybrid
    k : int
        Top-k documents
    alpha : float (0–1)
        Hybrid scoring weight
    reranker : bool
        Run cross-encoder reranker or not
    reranker_score : float
        Minimum threshold output of reranker
    store : str
        Store filtering ("jarir", "noon", "almanea")
    """

    img_bytes = await image.read() if image else None

    return pipeline.run(
        text=text,
        image_bytes=img_bytes,
        mode=mode,
        k=k,
        alpha=alpha,
        reranker=reranker,
        reranker_threshold=reranker_score,
        store=store,
    )
