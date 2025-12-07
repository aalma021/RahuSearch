import torch
from app.utils.logger import logger

def get_device():
    """Return 'cuda' or 'cpu' with logging & GPU VRAM info."""
    
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        props = torch.cuda.get_device_properties(0)

        total_vram = props.total_memory / (1024**3)

        logger.info(
            f"[Device] CUDA available → Using GPU: {gpu_name} ({total_vram:.1f} GB VRAM)"
        )

        return "cuda"

    logger.warning("[Device] CUDA not available → Falling back to CPU")
    return "cpu"
