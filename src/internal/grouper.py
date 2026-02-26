# -*- coding: utf-8 -*-
import numpy as np
from typing import List, Dict, Optional
from scipy.spatial import KDTree #type: ignore
from internal.ocr import TextBlock
from internal.config import PROXIMITY_RADIUS, KANJI_START, KANJI_END

class KanjiEntry:
    """Represents a grouped kanji entry with associated text."""
    def __init__(self, kanji: str, kanji_block: TextBlock):
        self.kanji = kanji
        self.kanji_block = kanji_block
        self.readings: List[str] = []
        self.meanings: List[str] = []
        self.examples: List[str] = []
        self.confidence: float = kanji_block.confidence
        
    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        return {
            'kanji': self.kanji,
            'readings': self.readings,
            'meanings': self.meanings,
            'examples': self.examples,
            'confidence': self.confidence
        }
    
    def add_reading(self, text: str):
        """Add a kana reading."""
        if text not in self.readings:
            self.readings.append(text)
    
    def add_meaning(self, text: str):
        """Add an English meaning."""
        if text not in self.meanings:
            self.meanings.append(text)
    
    def add_example(self, text: str):
        """Add an example sentence/word."""
        if text not in self.examples:
            self.examples.append(text)

class KanjiGrouper:
    """
    Groups OCR results into logical kanji entries using spatial proximity.
    Layout-agnostic approach that works with any format.
    """
    
    def __init__(self, proximity_radius: int = PROXIMITY_RADIUS):
        self.proximity_radius = proximity_radius
    
    def group_by_proximity(self, text_blocks: List[TextBlock]) -> List[KanjiEntry]:
        """
        Clusters text blocks that are spatially close to kanji anchors.
        
        Args:
            text_blocks: List of all detected text blocks
            
        Returns:
            List of KanjiEntry objects with associated text grouped
        """
        if not text_blocks:
            return []
        
        # Step 1: Identify kanji anchors (single kanji characters)
        kanji_blocks = self._identify_kanji_anchors(text_blocks)
        
        if not kanji_blocks:
            return []
        
        # Step 2: Build spatial index for efficient proximity search
        all_centers = [block.center for block in text_blocks]
        spatial_index = KDTree(all_centers)
        
        # Step 3: For each kanji, find and classify nearby text
        entries = []
        for kanji_block in kanji_blocks:
            entry = self._create_entry_with_nearby_text(
                kanji_block, text_blocks, spatial_index
            )
            if entry:
                entries.append(entry)
        
        return entries
    
    def _identify_kanji_anchors(self, text_blocks: List[TextBlock]) -> List[TextBlock]:
        """
        Find text blocks that are likely main kanji entries.
        
        Criteria:
        - Contains kanji characters
        - 1-3 characters long (single kanji or small compound)
        - Not purely kana or latin
        """
        kanji_anchors = []
        for block in text_blocks:
            text = block.text.strip()
            
            # Skip empty or too long
            if not text or len(text) > 3:
                continue
            
            # Must contain at least one kanji
            if not block.is_kanji:
                continue
            
            # For single character, must be kanji
            if len(text) == 1:
                if KANJI_START <= text <= KANJI_END:
                    kanji_anchors.append(block)
            else:
                # For 2-3 characters, at least half should be kanji
                kanji_count = sum(1 for c in text if KANJI_START <= c <= KANJI_END)
                if kanji_count >= len(text) / 2:
                    kanji_anchors.append(block)
        
        return kanji_anchors
    
    def _create_entry_with_nearby_text(
        self, 
        kanji_block: TextBlock, 
        all_blocks: List[TextBlock],
        spatial_index: KDTree
    ) -> Optional[KanjiEntry]:
        """
        Create a KanjiEntry by finding and classifying nearby text.
        
        Uses directional bias: prefers text to the right and below the kanji.
        """
        kanji_text = kanji_block.text.strip()
        entry = KanjiEntry(kanji_text, kanji_block)
        
        # Find nearby blocks using spatial index
        nearby_indices = spatial_index.query_ball_point(
            kanji_block.center, 
            self.proximity_radius
        )
        
        nearby_blocks = [all_blocks[i] for i in nearby_indices 
                        if all_blocks[i] != kanji_block]
        
        # Apply directional bias and classify nearby text
        kx, ky = kanji_block.center
        
        for block in nearby_blocks:
            bx, by = block.center
            
            # Directional bias: prefer right (bx > kx - 30) and below (by > ky - 30)
            # Allow slight left/above tolerance for OCR positioning errors
            if bx < kx - 30 and by < ky - 30:
                continue  # Skip blocks significantly to the left AND above
            
            # Classify based on content type
            text = block.text.strip()
            
            if block.is_kana:
                # Kana = readings
                entry.add_reading(text)
            elif block.is_latin:
                # Latin = meanings
                entry.add_meaning(text)
            elif block.is_kanji and len(text) > 3:
                # Long kanji text = examples
                entry.add_example(text)
            elif len(text) > 0:
                # Mixed content, try to classify by position
                # Text directly to the right (small Y difference) = likely reading
                if abs(by - ky) < 20 and bx > kx:
                    if block.is_kana:
                        entry.add_reading(text)
                    else:
                        entry.add_example(text)
                # Text below = likely example or meaning
                elif by > ky + 20:
                    if block.is_latin:
                        entry.add_meaning(text)
                    else:
                        entry.add_example(text)
        
        return entry
    
    def filter_entries_by_confidence(
        self, 
        entries: List[KanjiEntry], 
        min_confidence: float = 0.5
    ) -> List[KanjiEntry]:
        """Filter entries that don't meet minimum confidence threshold."""
        return [e for e in entries if e.confidence >= min_confidence]