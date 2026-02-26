# -*- coding: utf-8 -*-
import numpy as np
from typing import List, Dict, Tuple
from paddleocr import PaddleOCR  # type: ignore
from internal.config import (
    MIN_OCR_CONFIDENCE,
    KANJI_START, KANJI_END,
    HIRAGANA_START, HIRAGANA_END,
    KATAKANA_START, KATAKANA_END
)


class TextBlock:
    """Represents a single detected text block with metadata."""

    def __init__(self, bbox, text: str, confidence: float):
        self.bbox = bbox
        self.text = text
        self.confidence = confidence
        self.center = self._calculate_center(bbox)
        self.is_kanji = self._contains_kanji(text)
        self.is_kana = self._is_kana(text)
        self.is_latin = text.isascii()

    def _calculate_center(self, bbox) -> Tuple[float, float]:
        x_coords = [point[0] for point in bbox]
        y_coords = [point[1] for point in bbox]
        return (sum(x_coords) / len(x_coords), sum(y_coords) / len(y_coords))

    def _contains_kanji(self, text: str) -> bool:
        return any(KANJI_START <= char <= KANJI_END for char in text)

    def _is_kana(self, text: str) -> bool:
        return all(
            (HIRAGANA_START <= char <= HIRAGANA_END or
             KATAKANA_START <= char <= KATAKANA_END or
             char in 'ー・　 ()（）')
            for char in text
        )

    def to_dict(self) -> Dict:
        return {
            'text': self.text,
            'bbox': self.bbox,
            'center': self.center,
            'confidence': self.confidence,
            'is_kanji': self.is_kanji,
            'is_kana': self.is_kana,
            'is_latin': self.is_latin
        }


class SmartOCRService:
    """
    OCR service backed by PaddleOCR.
    Supports Japanese + English in a single pass.
    CPU-friendly — no CUDA required, but will use GPU if available.
    """

    def __init__(self, use_gpu: bool = False):
        print("Initializing PaddleOCR... (first run downloads models ~50MB)")
        # lang='japan' covers kanji/kana + romaji/English in one model
        import os
        os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

        self.reader = PaddleOCR(
            lang='japan',
            use_angle_cls=True,   # handles rotated/tilted text (important for photos)
            device='gpu' if use_gpu else 'cpu',
        )

    def extract_all_text_with_context(self, image: np.ndarray) -> List[TextBlock]:
        """
        Runs PaddleOCR and returns all detected text as TextBlock objects.

        PaddleOCR result format per line:
            [bbox, (text, confidence)]
        where bbox = [[x1,y1],[x2,y1],[x2,y2],[x1,y2]]
        """
        raw_results = self.reader.ocr(image, cls=True)

        text_blocks = []

        # PaddleOCR wraps results in an extra list layer
        if not raw_results or raw_results[0] is None:
            return text_blocks

        for line in raw_results[0]:
            bbox, (text, confidence) = line
            if confidence >= MIN_OCR_CONFIDENCE and text.strip():
                block = TextBlock(bbox, text.strip(), confidence)
                text_blocks.append(block)

        return text_blocks

    def filter_by_type(self, blocks: List[TextBlock],
                       kanji: bool = False,
                       kana: bool = False,
                       latin: bool = False) -> List[TextBlock]:
        """Filter text blocks by character type."""
        filtered = []
        for block in blocks:
            if kanji and block.is_kanji:
                filtered.append(block)
            elif kana and block.is_kana:
                filtered.append(block)
            elif latin and block.is_latin:
                filtered.append(block)
        return filtered