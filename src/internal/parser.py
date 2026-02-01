# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import Tuple, List, Optional, Dict
import re
from sudachipy import Dictionary, Tokenizer #type: ignore

class BaseParser(ABC):
    """Abstract base class for text parsers."""
    
    @abstractmethod
    def parse(self, text_block: str) -> Tuple[str, str, str, str]:
        """
        Parses a block of text into (Meaning, On-yomi, Kun-yomi, Example).
        
        Args:
            text_block: The raw text string containing all info.
            
        Returns:
            Tuple containing:
            - meaning: English meaning
            - on_yomi: On-yomi readings
            - kun_yomi: Kun-yomi readings
            - example: Example sentences/words
        """
        pass

class SudachiParser(BaseParser):
    """
    Parses text using SudachiPy morphological analysis and improved heuristics.
    Enhanced version of the original logic.
    """
    
    def __init__(self):
        try:
            self.tokenizer = Dictionary().create()
            self.available = True
        except Exception as e:
            print(f"Warning: Failed to initialize Sudachi Dictionary: {e}")
            self.tokenizer = None
            self.available = False

    def parse(self, text_block: str) -> Tuple[str, str, str, str]:
        """Parse text block into flashcard components."""
        if not text_block or not text_block.strip():
            return ('', '', '', '')
        
        # 1. Extract English Meaning (improved)
        meaning = self._extract_meaning(text_block)
        
        # 2. Extract Japanese Vocabulary & Readings
        vocab_list = re.findall(r'([\u3000-\u9faf\u3040-\u309f]+)\(([\u3040-\u309f\u30a0-\u30ff]+)\)', text_block)
        
        on_yomi_list = []
        kun_yomi_list = []
        
        for word, reading in vocab_list:
            # Count Kanji characters
            kanji_count = len(re.findall(r'[\u4e00-\u9faf]', word))
            
            # Improved classification
            if self._is_likely_onyomi(word, reading, kanji_count):
                # Convert to katakana for on-yomi style
                reading_kata = self._to_katakana(reading)
                on_yomi_list.append(f"{word}({reading_kata})")
            else:
                kun_yomi_list.append(f"{word}({reading})")

        # Deduplicate preserving order
        on_yomi = " ".join(dict.fromkeys(on_yomi_list))
        kun_yomi = " ".join(dict.fromkeys(kun_yomi_list))
        
        # 3. Example - extract longer Japanese text
        example = self._extract_example(text_block, vocab_list)
        
        return meaning, on_yomi, kun_yomi, example
    
    def _extract_meaning(self, text: str) -> str:
        """Extract English meaning with better handling."""
        # Find all sequences of English words (including hyphens, apostrophes)
        words = re.findall(r"[a-zA-Z][a-zA-Z\-']*", text)
        
        if not words:
            return ''
        
        # Join with spaces
        meaning = ' '.join(words)
        
        # Capitalize first letter
        if meaning:
            meaning = meaning[0].upper() + meaning[1:]
        
        return meaning
    
    def _is_likely_onyomi(self, word: str, reading: str, kanji_count: int) -> bool:
        """
        Improved heuristic for determining if reading is on-yomi.
        
        Rules:
        1. 2+ kanji = likely on-yomi (compounds)
        2. Reading in katakana = on-yomi
        3. Single kanji + short reading (1-2 mora) = might be on-yomi
        """
        # Rule 1: Multiple kanji
        if kanji_count >= 2:
            return True
        
        # Rule 2: Already in katakana
        if self._is_katakana(reading):
            return True
        
        # Rule 3: For single kanji, check reading length
        # On-yomi tend to be shorter (1-2 characters)
        if kanji_count == 1 and len(reading) <= 2:
            return True
        
        return False
    
    def _extract_example(self, text: str, vocab_list: List[Tuple[str, str]]) -> str:
        """Extract example sentence from text."""
        # Remove the vocab entries we already parsed
        example = text
        for word, reading in vocab_list:
            pattern = f"{word}\\({reading}\\)"
            example = re.sub(pattern, '', example)
        
        # Clean up
        example = re.sub(r'\s+', ' ', example).strip()
        
        # If no meaningful example remains, use the full text
        if not example or len(example) < 3:
            example = ' '.join(text.split())
        
        return example
    
    def _is_katakana(self, text: str) -> bool:
        """Check if text is primarily katakana."""
        if not text:
            return False
        katakana_count = sum(1 for c in text if '\u30a0' <= c <= '\u30ff')
        return katakana_count > len(text) / 2
    
    def _to_katakana(self, text: str) -> str:
        """Convert hiragana to katakana properly."""
        result = []
        for char in text:
            if '\u3040' <= char <= '\u309f':
                # Hiragana to katakana: add 0x60
                result.append(chr(ord(char) + 0x60))
            else:
                result.append(char)
        return ''.join(result)
    
    def _to_hiragana(self, text: str) -> str:
        """Convert katakana to hiragana."""
        result = []
        for char in text:
            if '\u30a0' <= char <= '\u30ff':
                # Katakana → Hiragana
                result.append(chr(ord(char) - 0x60))
            else:
                result.append(char)
        return ''.join(result)

    
    def get_kanji_info(self, kanji: str) -> Dict[str, any]:
        if not self.available or not self.tokenizer:
            return {'readings': {'on': [], 'kun': []}, 'meaning': ''}

        readings = {'on': set(), 'kun': set()}

        morphemes = self.tokenizer.tokenize(kanji)
        for m in morphemes:
            r = m.reading_form()
            if not r:
                continue

            # Heuristic (linguistically correct):
            # single-kanji verbs/adjectives → kun-yomi
            if len(kanji) == 1 and m.part_of_speech()[0] in ('動詞', '形容詞'):
                readings['kun'].add(self._to_hiragana(r))
            else:
                readings['on'].add(r)

        return {
            'readings': {
                'on': sorted(readings['on']),
                'kun': sorted(readings['kun'])
            },
            'meaning': ''
        }
