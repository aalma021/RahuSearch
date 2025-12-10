from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form
from app.pipeline.search_pipeline import SearchPipeline

router = APIRouter()
pipeline = SearchPipeline()


@router.post("/search")
async def search(
    text: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),

    mode: str = Form("hybrid"),
    k: int = Form(25),
    alpha: float = Form(0.5),
    reranker: bool = Form(True),
    reranker_score: float = Form(0.0),

    store: Optional[str] = Form(None),  # <<< EKLENDİ
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
        store=store
    )
