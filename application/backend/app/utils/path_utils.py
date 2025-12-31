import os
from app.config.settings import DATA_ROOT

# 🔥 HARDCODE YOK
BASE_IMAGE_URL = "/images"

_STORE_PATH_CACHE: dict[str, str] = {}
_CACHE_INITIALIZED = False


def _build_store_cache():
    global _CACHE_INITIALIZED, _STORE_PATH_CACHE

    if _CACHE_INITIALIZED:
        return

    _STORE_PATH_CACHE.clear()

    for entry in os.listdir(DATA_ROOT):
        entry_path = os.path.join(DATA_ROOT, entry)

        # CASE 1: datas/jarir
        if os.path.isdir(entry_path):
            _STORE_PATH_CACHE[entry.lower()] = entry
            continue

        # CASE 2: datas/data_1/jarir
        for store in os.listdir(entry_path):
            store_path = os.path.join(entry_path, store)
            if os.path.isdir(store_path):
                _STORE_PATH_CACHE[store.lower()] = os.path.relpath(
                    store_path, DATA_ROOT
                )

    _CACHE_INITIALIZED = True



def build_full_image_paths(store: str, image_paths: list[str]):
    if not image_paths or not store:
        return []

    _build_store_cache()

    relative_store_path = _STORE_PATH_CACHE.get(store.lower())
    if not relative_store_path:
        return []

    return [
        f"{BASE_IMAGE_URL}/{relative_store_path}/{p}"
        for p in image_paths
    ]
