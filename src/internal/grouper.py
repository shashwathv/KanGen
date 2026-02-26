# -*- coding: utf-8 -*-
from typing import List, Dict, Optional
from internal.ocr import TextBlock
from internal.config import KANJI_START, KANJI_END


class KanjiEntry:
    """Represents a single kanji extracted from the image."""

    def __init__(self, kanji: str, kanji_block: TextBlock):
        self.kanji = kanji
        self.kanji_block = kanji_block
        # These stay empty — readings/meanings come entirely from
        # Sudachi + LLM, not from the image layout.
        self.readings: List[str] = []
        self.meanings: List[str] = []
        self.examples: List[str] = []
        self.confidence: float = kanji_block.confidence

    def to_dict(self) -> Dict:
        return {
            'kanji': self.kanji,
            'readings': self.readings,
            'meanings': self.meanings,
            'examples': self.examples,
            'confidence': self.confidence
        }

    def add_reading(self, text: str):
        if text not in self.readings:
            self.readings.append(text)

    def add_meaning(self, text: str):
        if text not in self.meanings:
            self.meanings.append(text)

    def add_example(self, text: str):
        if text not in self.examples:
            self.examples.append(text)


class KanjiGrouper:
    """
    Layout-agnostic kanji extractor.

    Instead of trying to understand the image's spatial structure
    (columns, rows, proximity), this simply:
      1. Scans every OCR text block for kanji characters
      2. Deduplicates them
      3. Returns one KanjiEntry per unique kanji found

    All readings and meanings are then sourced from Sudachi + LLM,
    making the pipeline work on ANY image format — textbook pages,
    vocab lists, manga panels, signs, flashcards, etc.
    """

    def __init__(self, proximity_radius: int = 100):
        # proximity_radius kept for API compatibility but unused
        self.proximity_radius = proximity_radius

    def group_by_proximity(self, text_blocks: List[TextBlock]) -> List[KanjiEntry]:
        """
        Extract all unique kanji from OCR results.
        Name kept for compatibility with main.py call site.
        """
        return self.extract_kanji(text_blocks)

    def extract_kanji(self, text_blocks: List[TextBlock]) -> List[KanjiEntry]:
        """
        Walk every text block, pull out every kanji character,
        deduplicate, and return a KanjiEntry for each unique one.

        - Single-character kanji (e.g. 午, 書) → direct entry
        - Multi-kanji words (e.g. 受け入れる, 教会) → each kanji
          gets its own card so the deck covers individual characters
        - Pure kana / latin blocks → skipped entirely
        """
        seen: set = set()
        entries: List[KanjiEntry] = []

        for block in text_blocks:
            for char in block.text:
                if KANJI_START <= char <= KANJI_END and char not in seen:
                    seen.add(char)
                    entries.append(KanjiEntry(char, block))

        return entries

    def filter_entries_by_confidence(
        self,
        entries: List[KanjiEntry],
        min_confidence: float = 0.5
    ) -> List[KanjiEntry]:
        """Filter entries below a minimum OCR confidence threshold."""
        return [e for e in entries if e.confidence >= min_confidence]