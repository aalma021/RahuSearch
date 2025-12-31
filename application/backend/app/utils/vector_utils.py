import numpy as np


def cosine(a, b, eps: float = 1e-8) -> float:
    """
    Cosine similarity between two vectors.

    Args:
        a (list[float] | np.ndarray): query embedding
        b (list[float] | np.ndarray): document embedding
        eps (float): numerical stability epsilon

    Returns:
        float: cosine similarity in [-1, 1]
    """
    if a is None or b is None:
        return 0.0

    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)

    if a.shape != b.shape or a.size == 0:
        return 0.0

    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + eps
    return float(np.dot(a, b) / denom)
