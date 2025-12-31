import base64
from app.utils.logger import logger
from app.config.settings import IMAGE_TO_TEXT_MODEL

from app.openrouter.client import get_openrouter_client
from app.openrouter.prompts import IMAGE_TO_TEXT_PROMPT


class ImageProcessor:
    """
    Converts uploaded image bytes into a structured descriptive text block.
    """

    def __init__(self):
        self.client = get_openrouter_client()
        logger.info(
            "[ImageProcessor] Initialized using model=%s",
            IMAGE_TO_TEXT_MODEL,
        )

    def process(self, image_bytes: bytes) -> str:
        logger.debug("[ImageProcessor] Starting process()")

        if not image_bytes:
            logger.warning("[ImageProcessor] No image bytes provided.")
            return ""

        logger.debug("[ImageProcessor] Received %s bytes", len(image_bytes))

        encoded = base64.b64encode(image_bytes).decode("utf-8")

        response = self.client.chat.completions.create(
            model=IMAGE_TO_TEXT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": IMAGE_TO_TEXT_PROMPT,
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Analyze this product image and respond ONLY "
                                "with the strict JSON described in the system prompt."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{encoded}"
                            },
                        },
                    ],
                },
            ],
            temperature=0.2,
            extra_body={
                "usage": {
                    "include": True
                }
            },
        )

        content = response.choices[0].message.content

        if isinstance(content, list):
            text_parts = [
                c.get("text", "")
                for c in content
                if isinstance(c, dict) and c.get("type") == "text"
            ]
            result = "\n".join(text_parts).strip()
        else:
            result = (content or "").strip()

        logger.info("[ImageProcessor] Image converted to text: %s", result[:80])
        logger.debug("[ImageProcessor] Returning processed image text")

        return result
