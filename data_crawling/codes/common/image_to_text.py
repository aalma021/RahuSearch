import os
import time
import base64
from typing import List, Any

from openai import OpenAI
from dotenv import load_dotenv

# -------------------------------------------------
# ENV
# -------------------------------------------------
load_dotenv()

VISION_MODEL = os.getenv("IMAGE_TO_TEXT_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# image_to_text.py

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

VISION_PROMPT_PATH = os.path.join(BASE_DIR, "vision_prompt.txt")

MAX_RETRIES = int(os.getenv("IMAGE_TO_TEXT_RETRIES", "3"))
SLEEP_SEC = float(os.getenv("IMAGE_TO_TEXT_SLEEP", "0.2"))

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is required for image_to_text")

if not os.path.isfile(VISION_PROMPT_PATH):
    raise RuntimeError(f"VISION_PROMPT_PATH not found: {VISION_PROMPT_PATH}")

# -------------------------------------------------
# CLIENT
# -------------------------------------------------
client = OpenAI(api_key=OPENAI_API_KEY)

# -------------------------------------------------
# LOAD PROMPT (ONCE)
# -------------------------------------------------
with open(VISION_PROMPT_PATH, "r", encoding="utf-8") as f:
    VISION_PROMPT = f.read().strip()

if not VISION_PROMPT:
    raise RuntimeError("VISION_PROMPT is empty")

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def _encode_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# -------------------------------------------------
# MAIN API
# -------------------------------------------------
def image_to_text(image_paths: List[str]) -> List[Any]:
    """
    Takes local image paths and returns a list of outputs
    (one per image). Safe for partial failures.

    Prompt is loaded centrally from VISION_PROMPT_PATH.
    """

    results: List[Any] = []

    for idx, path in enumerate(image_paths):
        if not os.path.isfile(path):
            results.append(None)
            continue

        b64 = _encode_image(path)

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = client.responses.create(
                    model=VISION_MODEL,
                    instructions=VISION_PROMPT,
                    input=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "input_text",
                                    "text": (
                                        "Analyze this product image and return "
                                        "ONLY the JSON object."
                                    ),
                                },
                                {
                                    "type": "input_image",
                                    "image_url": (
                                        f"data:image/jpeg;base64,{b64}"
                                    ),
                                },
                            ],
                        }
                    ],
                )

                results.append(resp.output_text)
                break

            except Exception as e:
                if attempt == MAX_RETRIES:
                    results.append({
                        "_error": "vision_failed",
                        "_detail": str(e),
                        "_image": path,
                    })
                else:
                    time.sleep(attempt * 2)

        time.sleep(SLEEP_SEC)

    return results
