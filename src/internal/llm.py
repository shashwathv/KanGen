# -*- coding: utf-8 -*-
import json
import time
from typing import Tuple, Optional, Dict, List

from google import genai

from internal.parser import SudachiParser
from internal.validator import KanjiValidator
from internal.grouper import KanjiEntry
from internal.config import VALIDATION_CONFIDENCE_THRESHOLD


BATCH_SIZE = 5  # SAFE for free tier


class EnhancedCard:
    def __init__(self, kanji: str, meaning: str, on_yomi: str, kun_yomi: str, example: str):
        self.kanji = kanji
        self.meaning = meaning
        self.on_yomi = on_yomi
        self.kun_yomi = kun_yomi
        self.example = example

    def to_tuple(self) -> Tuple[str, str, str, str, str]:
        return (self.kanji, self.meaning, self.on_yomi, self.kun_yomi, self.example)


class LLMEnhancer:
    """
    BATCHED Gemini enhancer.
    One request handles multiple kanji.
    """
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash"

    def enhance_batch(
        self,
        batch: List[KanjiEntry],
        sudachi_map: Dict[str, Dict]
    ) -> Dict[str, Tuple[str, str, str, str]]:
        """
        Returns:
            { kanji: (meaning, on, kun, example) }
        """
        prompt_blocks = []

        for i, entry in enumerate(batch, 1):
            s = sudachi_map[entry.kanji]
            prompt_blocks.append(f"""
{i}.
Kanji: {entry.kanji}
On-yomi (Katakana): {', '.join(s['readings']['on']) or '(none)'}
Kun-yomi (Hiragana): {', '.join(s['readings']['kun']) or '(none)'}
""")

        prompt = f"""
You are a Japanese linguistics expert creating Anki flashcards.

For EACH kanji below, generate flashcard data.

RULES (MANDATORY):
- Use ONLY the readings provided.
- If a Kun-yomi exists, it MUST appear.
- If an On-yomi exists, it MUST appear.
- Do NOT invent readings.
- On-yomi MUST be Katakana.
- Kun-yomi MUST be Hiragana.
- Prefer Kun-yomi usage in example sentences.

KANJI LIST:
{''.join(prompt_blocks)}

OUTPUT FORMAT (STRICT JSON ARRAY):
[
  {{
    "kanji": "漢字",
    "meaning": "English meaning",
    "on_yomi": "カタカナ",
    "kun_yomi": "ひらがな",
    "example": "日本語の例文"
  }}
]
"""

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )

        clean = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)

        result = {}
        for item in data:
            result[item["kanji"]] = (
                item.get("meaning", "").strip(),
                item.get("on_yomi", "").strip(),
                item.get("kun_yomi", "").strip(),
                item.get("example", "").strip(),
            )

        return result


class SmartEnhancer:
    """
    Batch-aware enhancement engine.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.llm = LLMEnhancer(api_key) if api_key else None
        self.sudachi = SudachiParser()
        self.validator = KanjiValidator()

    def enhance_all(self, entries: List[KanjiEntry]) -> List[EnhancedCard]:
        sudachi_map = {
            e.kanji: self.sudachi.get_kanji_info(e.kanji)
            for e in entries
        }

        cards: List[EnhancedCard] = []

        for i in range(0, len(entries), BATCH_SIZE):
            batch = entries[i:i + BATCH_SIZE]

            try:
                if self.llm:
                    llm_results = self.llm.enhance_batch(batch, sudachi_map)
                else:
                    llm_results = {}

            except Exception as e:
                print(f"⚠️ LLM batch failed, falling back: {e}")
                llm_results = {}

            for entry in batch:
                s = sudachi_map[entry.kanji]
                on_list = s["readings"]["on"]
                kun_list = s["readings"]["kun"]

                meaning, on, kun, ex = llm_results.get(entry.kanji, ("", "", "", ""))

                # HARD FALLBACKS
                if not on and on_list:
                    on = on_list[0]
                if not kun and kun_list:
                    kun = kun_list[0]
                if not meaning:
                    meaning = " ".join(entry.meanings)

                if not meaning:
                    continue

                cards.append(
                    EnhancedCard(entry.kanji, meaning, on, kun, ex)
                )

            time.sleep(1.2)  # RPM safety buffer

        return cards
        
    def enhance(self, entry: KanjiEntry) -> Optional[EnhancedCard]:
        """
        Backward-compatible single-entry API.
        Internally uses batch logic.
        """
        cards = self.enhance_all([entry])
        return cards[0] if cards else None



class HybridParser:
    """
    Compatibility layer.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.enhancer = SmartEnhancer(api_key)

    def parse(self, text_block: str) -> Tuple[str, str, str, str]:
        return ('', '', '', '')
