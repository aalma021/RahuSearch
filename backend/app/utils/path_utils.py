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

    for data_dir in os.listdir(DATA_ROOT):
        data_dir_path = os.path.join(DATA_ROOT, data_dir)
        if not os.path.isdir(data_dir_path):
            continue

        for store in os.listdir(data_dir_path):
            store_path = os.path.join(data_dir_path, store)
            if not os.path.isdir(store_path):
                continue

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
