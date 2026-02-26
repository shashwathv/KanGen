# -*- coding: utf-8 -*-
import json
import re
import time
from typing import Tuple, Optional, Dict, List

from google import genai

from internal.parser import SudachiParser
from internal.validator import KanjiValidator
from internal.grouper import KanjiEntry
from internal.config import VALIDATION_CONFIDENCE_THRESHOLD


BATCH_SIZE = 500  # Send all kanji in one request — fits easily in Gemini's context window


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
    Single-request Gemini enhancer.
    All kanji go in one API call regardless of count.
    """
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash"

    def _clean(self, val) -> str:
        """Handle None, null, and literal 'none' strings from Gemini."""
        if val is None:
            return ""
        v = str(val).strip()
        return "" if v.lower() in ("none", "(none)", "n/a", "null", "") else v

    def _parse_retry_delay(self, error_str: str) -> int:
        """Extract retry delay in seconds from a 429 error message."""
        match = re.search(r"retryDelay.*?(\d+)s", error_str)
        return int(match.group(1)) if match else 60

    def enhance_batch(
        self,
        batch: List[KanjiEntry],
        sudachi_map: Dict[str, Dict]
    ) -> Dict[str, Tuple[str, str, str, str]]:
        """
        Send all kanji in one prompt.
        Returns: { kanji: (meaning, on_yomi, kun_yomi, example) }
        """
        prompt_blocks = []

        for i, entry in enumerate(batch, 1):
            s = sudachi_map[entry.kanji]
            on_readings = ", ".join(s["readings"]["on"]) or "(none)"
            kun_readings = ", ".join(s["readings"]["kun"]) or "(none)"
            prompt_blocks.append(
                f"{i}.\nKanji: {entry.kanji}\n"
                f"On-yomi (Katakana): {on_readings}\n"
                f"Kun-yomi (Hiragana): {kun_readings}\n"
            )

        prompt = f"""You are a Japanese linguistics expert creating Anki flashcards.

For EACH kanji below, produce flashcard data.

MANDATORY RULES:
- Use ONLY the readings provided — do NOT invent readings.
- On-yomi MUST be written in Katakana only.
- Kun-yomi MUST be written in Hiragana only.
- If a reading field has no value, output an empty string "" — NEVER output the word "none", "null", or "n/a".
- Do NOT mix on-yomi into the kun-yomi field or vice versa.
- Meaning must be a concise English definition.
- Example must be a natural Japanese sentence using the kanji.

KANJI LIST:
{''.join(prompt_blocks)}

OUTPUT FORMAT — strict JSON array, no markdown, no preamble:
[
  {{
    "kanji": "漢字",
    "meaning": "English meaning",
    "on_yomi": "カタカナ",
    "kun_yomi": "ひらがな",
    "example": "日本語の例文"
  }}
]"""

        def _do_request():
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            clean = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)

            result = {}
            for item in data:
                result[item["kanji"]] = (
                    self._clean(item.get("meaning")),
                    self._clean(item.get("on_yomi")),
                    self._clean(item.get("kun_yomi")),
                    self._clean(item.get("example")),
                )
            return result

        # First attempt
        try:
            return _do_request()
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                delay = self._parse_retry_delay(error_str) + 2
                print(f"⏳ Rate limited. Waiting {delay}s before retry...")
                time.sleep(delay)
                try:
                    return _do_request()
                except Exception as e2:
                    raise Exception(f"429 RESOURCE_EXHAUSTED after retry: {e2}")
            else:
                raise


class SmartEnhancer:
    """
    Batch-aware enhancement engine.
    Sends all kanji in a single API request.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.llm = LLMEnhancer(api_key) if api_key else None
        self.sudachi = SudachiParser()
        self.validator = KanjiValidator()

    def enhance_all(self, entries: List[KanjiEntry]) -> List[EnhancedCard]:
        # Build Sudachi data for all entries upfront
        sudachi_map = {
            e.kanji: self.sudachi.get_kanji_info(e.kanji)
            for e in entries
        }

        cards: List[EnhancedCard] = []

        # Process in chunks of BATCH_SIZE (effectively one chunk for normal use)
        for i in range(0, len(entries), BATCH_SIZE):
            batch = entries[i:i + BATCH_SIZE]

            try:
                if self.llm:
                    llm_results = self.llm.enhance_batch(batch, sudachi_map)
                else:
                    llm_results = {}
            except Exception as e:
                print(f"⚠️ LLM batch failed, falling back to Sudachi only: {e}")
                llm_results = {}

            for entry in batch:
                s = sudachi_map[entry.kanji]
                on_list = s["readings"]["on"]
                kun_list = s["readings"]["kun"]

                meaning, on, kun, ex = llm_results.get(entry.kanji, ("", "", "", ""))

                # Fallback to Sudachi if LLM gave nothing
                if not on and on_list:
                    on = on_list[0]
                if not kun and kun_list:
                    kun = kun_list[0]
                if not meaning:
                    meaning = " ".join(entry.meanings)

                # Skip cards with no meaning at all
                if not meaning:
                    continue

                cards.append(EnhancedCard(entry.kanji, meaning, on, kun, ex))

        return cards

    def enhance(self, entry: KanjiEntry) -> Optional[EnhancedCard]:
        """Backward-compatible single-entry API."""
        cards = self.enhance_all([entry])
        return cards[0] if cards else None


class HybridParser:
    """Compatibility layer."""
    def __init__(self, api_key: Optional[str] = None):
        self.enhancer = SmartEnhancer(api_key)

    def parse(self, text_block: str) -> Tuple[str, str, str, str]:
        return ('', '', '', '')