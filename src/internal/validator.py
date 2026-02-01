# -*- coding: utf-8 -*-
import re
from typing import Dict, List, Tuple
from sudachipy import Dictionary, Tokenizer  #type: ignore
from kangen.grouper import KanjiEntry
from kangen.config import VALIDATION_CONFIDENCE_THRESHOLD

class ValidationResult:
    """Result of validating a kanji entry."""
    def __init__(self, is_valid: bool, confidence: float, issues: List[str], corrections: Dict):
        self.is_valid = is_valid
        self.confidence = confidence
        self.issues = issues
        self.corrections = corrections
    
    def to_dict(self) -> Dict:
        return {
            'is_valid': self.is_valid,
            'confidence': self.confidence,
            'issues': self.issues,
            'corrections': self.corrections
        }

class KanjiValidator:
    """
    Validates if grouped kanji + readings are linguistically correct.
    Uses Sudachi morphological analyzer for verification.
    """
    
    def __init__(self):
        try:
            self.tokenizer = Dictionary().create()
            self.available = True
        except Exception as e:
            print(f"Warning: Failed to initialize Sudachi Dictionary: {e}")
            self.tokenizer = None
            self.available = False
    
    def validate_entry(self, entry: KanjiEntry) -> ValidationResult:
        """
        Checks if readings match the kanji using dictionary lookup.
        
        Returns:
            ValidationResult with is_valid flag, confidence score, and suggestions
        """
        if not self.available:
            # If Sudachi not available, assume valid but low confidence
            return ValidationResult(
                is_valid=True,
                confidence=0.5,
                issues=["Sudachi dictionary not available for validation"],
                corrections={}
            )
        
        kanji = entry.kanji
        readings = entry.readings
        
        # Get valid readings from dictionary
        valid_readings = self._get_valid_readings_for_kanji(kanji)
        
        # Check which OCR readings match dictionary
        matched_readings = []
        unmatched_readings = []
        
        for reading in readings:
            # Clean reading (remove parentheses, spaces, special chars)
            clean = re.sub(r'[()（）　 ・ー]', '', reading)
            
            if self._reading_matches_kanji(clean, valid_readings):
                matched_readings.append(reading)
            else:
                unmatched_readings.append(reading)
        
        # Calculate confidence and validity
        if not readings:
            is_valid = False
            confidence = 0.0
            issues = ["No readings detected"]
        elif matched_readings:
            is_valid = True
            confidence = len(matched_readings) / len(readings)
            issues = []
            if unmatched_readings:
                issues.append(f"Some readings don't match: {unmatched_readings}")
        else:
            is_valid = False
            confidence = 0.0
            issues = ["No valid readings found for this kanji"]
        
        corrections = {
            'valid_readings': valid_readings,
            'matched': matched_readings,
            'unmatched': unmatched_readings
        }
        
        return ValidationResult(is_valid, confidence, issues, corrections)
    
    def _get_valid_readings_for_kanji(self, kanji: str) -> Dict[str, List[str]]:
        """
        Use Sudachi to get all possible readings for a kanji.
        
        Returns:
            Dict with 'on' and 'kun' reading lists
        """
        if not self.tokenizer:
            return {'on': [], 'kun': []}
        
        try:
            # Tokenize the kanji
            morphemes = self.tokenizer.tokenize(kanji)
            
            readings = {'on': [], 'kun': []}
            
            for m in morphemes:
                reading = m.reading_form()
                
                if not reading:
                    continue
                
                # Store both hiragana and katakana versions
                reading_hira = self._to_hiragana(reading)
                reading_kata = self._to_katakana(reading)
                
                # Heuristic: if dictionary gives katakana, it's likely on-yomi
                if self._is_katakana(reading):
                    readings['on'].append(reading_kata)
                    readings['on'].append(reading_hira)
                else:
                    readings['kun'].append(reading_hira)
                    readings['kun'].append(reading_kata)
            
            # Remove duplicates
            readings['on'] = list(set(readings['on']))
            readings['kun'] = list(set(readings['kun']))
            
            return readings
            
        except Exception as e:
            print(f"Warning: Sudachi lookup failed for '{kanji}': {e}")
            return {'on': [], 'kun': []}
    
    def _reading_matches_kanji(self, reading: str, valid_readings: Dict[str, List[str]]) -> bool:
        """Check if a reading is valid for this kanji."""
        all_valid = valid_readings['on'] + valid_readings['kun']
        
        # Try both hiragana and katakana versions
        reading_hira = self._to_hiragana(reading)
        reading_kata = self._to_katakana(reading)
        
        return (reading in all_valid or 
                reading_hira in all_valid or 
                reading_kata in all_valid)
    
    def _is_katakana(self, text: str) -> bool:
        """Check if text is primarily katakana."""
        if not text:
            return False
        katakana_count = sum(1 for c in text if '\u30a0' <= c <= '\u30ff')
        return katakana_count > len(text) / 2
    
    def _to_hiragana(self, text: str) -> str:
        """Convert katakana to hiragana."""
        result = []
        for char in text:
            if '\u30a0' <= char <= '\u30ff':
                # Katakana to hiragana: subtract 0x60
                result.append(chr(ord(char) - 0x60))
            else:
                result.append(char)
        return ''.join(result)
    
    def _to_katakana(self, text: str) -> str:
        """Convert hiragana to katakana."""
        result = []
        for char in text:
            if '\u3040' <= char <= '\u309f':
                # Hiragana to katakana: add 0x60
                result.append(chr(ord(char) + 0x60))
            else:
                result.append(char)
        return ''.join(result)