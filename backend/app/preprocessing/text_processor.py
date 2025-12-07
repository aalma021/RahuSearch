import re
from app.utils.logger import logger

class TextProcessor:
    def process(self, text: str) -> str:
        """
        Normalize raw user text:
        - strip whitespace
        - remove repeated spaces
        - lowercase is OPTIONAL (do NOT enforce)
        """

        logger.debug("[TextProcessor] process() called")

        if not text:
            logger.warning("[TextProcessor] Empty or null text received")
            return ""

        original = text
        text = text.strip()
        text = re.sub(r"\s+", " ", text)

        logger.info("[TextProcessor] Text normalized (orig: %s | new: %s)", original[:40], text[:40])

        return text
