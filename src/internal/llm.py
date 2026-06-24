import time
import logging
import os
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from PIL import Image

from internal.validator import KanjiValidator

logger = logging.getLogger(__name__)

class KanjiCard(BaseModel):
    kanji: str
    meaning: str
    on_yomi: str = Field(description="katakana, empty string if none")
    kun_yomi: str = Field(description="hiragana, empty string if none")
    example: str


class VisionEnhancer:
    def __init__(self, api_key: Optional[str] = None):
        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY is required.")

        self.client = genai.Client(api_key=key)
        self.validator = KanjiValidator()

    def extract_cards_from_image(self, image_path: str) -> List[KanjiCard]:
        prompt = """This is a photo of a Japanese textbook page or study sheet.
            Identify every distinct kanji that is presented as a vocabulary/study item.
            Ignore stroke-order diagrams, furigana pronunciation guides, and grid practice boxes.
            For each kanji return: the character, English meaning, on-yomi (katakana), kun-yomi (hiragana), and one natural example sentence.
            If example sentences appear on the page, prefer those; otherwise generate one."""

        max_retries = 5

        for attempt in range(max_retries):
            try:
                image = Image.open(image_path)
                response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[prompt, image],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=list[KanjiCard],
                        temperature=0.1,  # Keep it highly deterministic
                    ),
                )

                cards = response.parsed
                if not cards:
                    return []

                valid_cards = []
                for card in cards:
                    validation = self.validator.validate_entry(
                        card.kanji, [card.on_yomi, card.kun_yomi]
                    )
                    if not validation.is_valid:
                        logger.debug("Reading flagged for %s: %s", card.kanji, validation.issues)
                        if validation.suggested_on:
                            logger.debug("Correcting on-yomi for %s: %s -> %s",
                                         card.kanji, card.on_yomi, validation.suggested_on)
                            card.on_yomi = validation.suggested_on
                        if validation.suggested_kun:
                            logger.debug("Correcting kun-yomi for %s: %s -> %s",
                                         card.kanji, card.kun_yomi, validation.suggested_kun)
                            card.kun_yomi = validation.suggested_kun
                    valid_cards.append(card)
                return valid_cards

            except Exception as e:
                err = str(e)
                is_retryable = "429" in err or "RESOURCE_EXHAUSTED" in err or "503" in err
                logger.warning("Gemini extraction failed (attempt: %d): %s", attempt +1, e)
                if is_retryable and attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))
                    continue
                return []

        return []