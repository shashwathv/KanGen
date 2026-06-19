import time
import os 
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from PIL import Image

from internal.validator import KanjiValidator

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
        
        self.client = genai.Client(api_key=api_key)
        self.validator = KanjiValidator()

    def extract_cards_from_image(self,image_path: str) -> List[KanjiCard]:
        prompt = """This is a photo of a Japanese textbook page or study sheet.
            Identify every distinct kanji that is presented as a vocabulary/study item.
            Ignore stroke-order diagrams, furigana pronunciation guides, and grid practice boxes.
            For each kanji return: the character, English meaning, on-yomi (katakana), kun-yomi (hiragana), and one natural example sentence.
            If example sentences appear on the page, prefer those; otherwise generate one."""
        
        max_retries = 3

        for attempt in range(max_retries):
            try:
                image = Image.open(image_path)

                response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[prompt, image],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=list[KanjiCard],
                        temperature=0.1 # Keep it highly deterministic
                    ),
                )

                cards = response.parsed
                valid_cards = []

                for card in cards:
                    validation = self.validator.validate_entry(card.kanji, [card.on_yomi, card.kun_yomi])
                    if not validation.is_valid:
                        print(f"!!! Validation warning for card {card.kanji}: {validation.issues}")
                    valid_cards.append(card)
                
                return valid_cards
            
            except Exception as e:
                print(f"!!! Gemini Extraction Failed: {e} !!!")
                return []
            
        print(f"!!! Max retries reached. Gemini is still unavailable !!!")
        return []