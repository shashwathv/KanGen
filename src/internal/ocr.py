# -*- coding: utf-8 -*-
import easyocr #type: ignore
import numpy as np
from typing import List, Dict, Tuple
from kangen.config import (
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
        """Calculate center point of bounding box."""
        x_coords = [point[0] for point in bbox]
        y_coords = [point[1] for point in bbox]
        return (sum(x_coords) / 4, sum(y_coords) / 4)
    
    def _contains_kanji(self, text: str) -> bool:
        """Check if text contains any kanji characters."""
        return any(KANJI_START <= char <= KANJI_END for char in text)
    
    def _is_kana(self, text: str) -> bool:
        """Check if text is purely hiragana or katakana."""
        return all(
            (HIRAGANA_START <= char <= HIRAGANA_END or 
             KATAKANA_START <= char <= KATAKANA_END or
             char in 'ー・　 ()（）')
            for char in text
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
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
    Enhanced OCR service that extracts all text with linguistic context.
    No assumptions about layout or column structure.
    """
    
    def __init__(self, use_gpu: bool = False):
        print("Initializing EasyOCR... (this may take a moment)")
        self.reader = easyocr.Reader(['ja', 'en'], gpu=use_gpu)

    def extract_all_text_with_context(self, image: np.ndarray) -> List[TextBlock]:
        """
        Runs OCR and returns all detected text with linguistic metadata.
        
        Returns:
            List of TextBlock objects containing text, position, and classification.
        """
        # Run OCR with detail=1 to get (bbox, text, confidence)
        raw_results = self.reader.readtext(image, detail=1)
        
        # Filter by confidence and convert to TextBlock objects
        text_blocks = []
        for (bbox, text, confidence) in raw_results:
            if confidence >= MIN_OCR_CONFIDENCE:
                block = TextBlock(bbox, text, confidence)
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