import base64
from app.config.settings import IMAGE_TO_TEXT_MODEL, OPENAI_API_KEY
from app.utils.logger import logger

from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

IMAGE_TO_TEXT_PROMPT = """
You are an e-commerce vision assistant for a semantic search system.

Goal:
- Look at ONE product image.
- Produce a compact, machine-readable JSON description optimized for embedding-based retrieval.
- Your JSON will be indexed and used for nearest-neighbor search (vector + BM25).

Very important guidelines:
- Focus ONLY on the main product, ignore:
  - Backgrounds
  - Logos (unless they are clearly part of the product design)
  - UI elements, price tags, discount labels, watermarks
- Do NOT invent brand or model names unless clearly visible as text.
- Think in terms of search keywords: what would a user type to find this product?

Field semantics:
- "short_caption": 
  - 1 short sentence (max ~25 tokens)
  - Natural language, but dense in useful keywords.
  - Example style: "wireless over-ear headphones, dark blue, cushioned headband for music and gaming"

- "visual_keywords":
  - 8–20 short phrases, lower_case, very useful as tokens for semantic search.
  - Prefer generic, reusable keywords like:
    - "electronics", "smartphone", "iphone-style phone", "orange", "glass back", 
      "rounded corners", "dual camera", "gaming headset", "office chair", etc.
  - Mix of:
    - product type (smartphone, headphones, laptop, tv, speaker, mouse, keyboard, etc.)
    - color and material (orange, black, plastic, metal, leather, fabric, glass)
    - form factor (slim, compact, over-ear, in-ear, rectangular, curved)
    - use case (gaming, office, work, school, travel, kids, sports, music)
  - Each keyword should be 1–3 words (no long sentences).

- "attributes":
  - "product_type": a single short phrase, e.g. "smartphone", "over-ear headphones", "office chair"
  - "main_color": one color word, e.g. "orange", "black", "silver"
  - "secondary_color": second main visible color or null
  - "material": list of short tokens, e.g. ["plastic", "glass"] or ["fabric", "metal"]
  - "style": list like ["minimalist", "gaming", "business", "sporty", "kids"]
  - "category_hint": list of possible catalog categories, e.g. ["electronics", "mobile phones"]
  - "special_features": list of notable features, e.g. ["wireless", "noise cancelling", "water resistant"]
  - "visible_text": list of any clearly readable words on the product (logos, labels, buttons). If nothing is readable, use [].

Output format rules:
- Return STRICT JSON, NO extra text, NO explanations.
- Use only double quotes.
- Do NOT add trailing commas.
- Make sure the JSON is syntactically valid.

Example of the desired STYLE (just an example, do NOT copy values blindly):

{
  "short_caption": "orange smartphone with rounded edges and dual rear camera",
  "visual_keywords": [
    "electronics",
    "smartphone",
    "orange phone",
    "dual camera",
    "rounded corners",
    "touchscreen",
    "glass front",
    "slim design"
  ],
  "attributes": {
    "product_type": "smartphone",
    "main_color": "orange",
    "secondary_color": "black",
    "material": ["glass", "plastic"],
    "style": ["modern", "minimalist"],
    "category_hint": ["electronics", "mobile phones"],
    "special_features": ["touchscreen"],
    "visible_text": []
  }
}

Now look at the image and produce ONLY one JSON object with the exact keys:
"short_caption", "visual_keywords", "attributes".
"""

class ImageProcessor:
    """
    Converts uploaded image bytes into a structured descriptive text block.
    """

    def __init__(self):
        logger.info("[ImageProcessor] Initialized using model: %s", IMAGE_TO_TEXT_MODEL)

    def process(self, image_bytes: bytes) -> str:
        logger.debug("[ImageProcessor] Starting process()")

        if not image_bytes:
            logger.warning("[ImageProcessor] No image bytes provided.")
            return ""

        logger.debug("[ImageProcessor] Received %s bytes", len(image_bytes))

        # Base64 encode
        encoded = base64.b64encode(image_bytes).decode("utf-8")

        # OpenAI Vision via chat.completions
        response = client.chat.completions.create(
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
                            "text": "Analyze this product image and respond ONLY with the strict JSON described in the system prompt."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{encoded}"
                            }
                        }
                    ],
                },
            ],
        )

        # Sonucu al
        content = response.choices[0].message.content
        # Bazı SDK sürümlerinde content direkt string, bazılarında list olabilir.
        if isinstance(content, list):
            # text parçalarını birleştir
            text_parts = [c.get("text", "") for c in content if c.get("type") == "text"]
            result = "\n".join(text_parts).strip()
        else:
            result = (content or "").strip()

        logger.info("[ImageProcessor] Image converted to text: %s", result[:80])
        logger.debug("[ImageProcessor] Returning processed image text")

        return result

