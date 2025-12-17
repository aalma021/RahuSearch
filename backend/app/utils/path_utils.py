import os
from app.config.settings import DATA_ROOT

BASE_IMAGE_URL = "http://localhost:8000/images"

# store -> relative path (data_3/noon gibi)
_STORE_PATH_CACHE: dict[str, str] = {}
_CACHE_INITIALIZED = False


def _build_store_cache():
    """
    Build store cache ONCE per app lifecycle.
    Cache is reset on every app restart.

    Expected structure:
    DATA_ROOT/
      ├── data_1/jarir/
      ├── data_2/extra/
      ├── data_3/noon/
    """

    global _CACHE_INITIALIZED, _STORE_PATH_CACHE

    if _CACHE_INITIALIZED:
        return

    _STORE_PATH_CACHE.clear()  # 🔥 garanti sıfırlama

    for data_dir in os.listdir(DATA_ROOT):
        data_dir_path = os.path.join(DATA_ROOT, data_dir)

        if not os.path.isdir(data_dir_path):
            continue

        # data_1, data_2, data_3
        for store in os.listdir(data_dir_path):
            store_path = os.path.join(data_dir_path, store)

            if not os.path.isdir(store_path):
                continue

            # jarir -> data_1/jarir
            _STORE_PATH_CACHE[store.lower()] = os.path.relpath(
                store_path, DATA_ROOT
            )

    _CACHE_INITIALIZED = True


def build_full_image_paths(store: str, image_paths: list[str]):
    """
    Build public image URLs.

    store: "noon"
    image_paths:
      ["Accessories/abc/01.jpg", "Accessories/abc/02.jpg"]
    """

    if not image_paths or not store:
        return []

    _build_store_cache()

    store_key = store.lower()
    relative_store_path = _STORE_PATH_CACHE.get(store_key)

    if not relative_store_path:
        return []

    return [
        f"{BASE_IMAGE_URL}/{relative_store_path}/{p}"
        for p in image_paths
    ]
