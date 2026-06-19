import re
from typing import List
from sudachipy import Dictionary

class ValidationResult:
    def __init__(self, is_valid: bool, issues: List[str]):
        self.is_valid = is_valid
        self.issues = issues

class KanjiValidator:
    def __init__(self):
        try:
            self.tokenizer = Dictionary().create()
            self.available = True
        except Exception as e:
            print(f"!!! Warning: Failed to initialze Sudachi: {e}")
            self.available = False

    def validate_entry(self, kanji: str, proposed_readings: List[str]) -> ValidationResult:
        if not self.available:
            return ValidationResult(True, ["!!! Sudachipy Failed !!!"])
        
        valid_readings = self._get_valid_readings(kanji)
        issues = []

        for reading in proposed_readings:
            if not reading.strip():
                continue

            clean = re.sub(r'[()（）  ・ー]', '', reading)
            reading_h = self._to_hiragana(clean)
            reading_k = self._to_katakana(clean)

            if not (clean in valid_readings or reading_h in valid_readings or reading_k in valid_readings):
                issues.append(f"Unusual reading detected: {reading}")
            
        return ValidationResult(len(issues)== 0, issues)
    
    def _get_valid_readings(self, kanji: str) -> List[str]:
        if not self.tokenizer: return []
        try:
            morphemes = self.tokenizer.tokenize(kanji)
            readings = []
            for m in morphemes:
                r = m.reading_form()
                if r:
                    readings.extend([self._to_hiragana(r), self._to_katakana(r)])
            return list(set(readings))
        
        except:
            return []
        
    def _to_hiragana(self, text: str) -> str:
        return ''.join(chr(ord(c) - 0x60) if '\u30a0' <= c <= '\u30ff' else c for c in text)
    
    def _to_katakana(self, text: str) -> str:
        return ''.join(chr(ord(c) + 0x60) if '\u3040' <= c <= '\u309f' else c for c in text)