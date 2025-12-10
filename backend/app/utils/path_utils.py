import os
from app.config.settings import DATA_ROOT

BASE_IMAGE_URL = "http://localhost:8000/images"

# Cache dictionary (store → relative_path)
_STORE_PATH_CACHE = {}
_STORE_SCAN_DONE = False


def _build_store_cache():
    """
    Scan DATA_ROOT once and populate cache:
    example cache:
    {
        'jarir': 'data_1/jarir',
        'noon': 'data_3/noon',
        'extra': 'data_2/extra'
    }
    """
    global _STORE_SCAN_DONE
    if _STORE_SCAN_DONE:
        return

    for root, dirs, files in os.walk(DATA_ROOT):
        for d in dirs:
            key = d.lower()
            # relative path
            rel = os.path.relpath(os.path.join(root, d), DATA_ROOT)
            _STORE_PATH_CACHE[key] = rel

    _STORE_SCAN_DONE = True


def build_full_image_paths(store: str, image_paths):
    if not image_paths or not store:
        return []

    # ensure cache exists
    _build_store_cache()

    store_lower = store.lower()

    # fast dictionary lookup
    relative_path = _STORE_PATH_CACHE.get(store_lower)
    if not relative_path:  
        return []

    urls = []
    for p in image_paths:
        urls.append(f"{BASE_IMAGE_URL}/{relative_path}/{p}")

    return urls