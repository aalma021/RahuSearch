from app.utils.logger import logger

class InputRouter:
    def merge(self, text: str = None, image_text: str = None) -> str:
        """
        Final input text for semantic search.
        Both text and image-text can be present.
        """
        logger.debug("[InputRouter] merge() called")

        parts = []

        if text:
            logger.debug("[InputRouter] Text input detected: %s", text[:50])
            parts.append(text)
        else:
            logger.debug("[InputRouter] No text input provided")

        if image_text:
            logger.debug("[InputRouter] Image-text input detected: %s", image_text[:50])
            parts.append(image_text)
        else:
            logger.debug("[InputRouter] No image-text input provided")

        merged = " ".join(parts).strip()
        logger.info("[InputRouter] Final merged input length: %s", len(merged))

        return merged
