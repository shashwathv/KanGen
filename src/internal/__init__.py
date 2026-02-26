# -*- coding: utf-8 -*-
"""
KanGen - Kanji Flashcard Generator

Smart Architecture v2.0:
- Layout-agnostic OCR processing
- Spatial proximity grouping
- Dictionary-based validation
- Self-correcting AI enhancement
"""
__version__ = "2.0.0"

from internal.ocr import SmartOCRService, TextBlock
from internal.grouper import KanjiGrouper, KanjiEntry
from internal.validator import KanjiValidator, ValidationResult
from internal.llm import SmartEnhancer, EnhancedCard, HybridParser
from internal.anki import AnkiGenerator
from internal.image_processing import (
    convert_heic_to_jpeg,
    load_image,
    find_table_contour,
    warp_perspective,
    save_debug_image
)

__all__ = [
    'SmartOCRService',
    'TextBlock',
    'KanjiGrouper',
    'KanjiEntry',
    'KanjiValidator',
    'ValidationResult',
    'SmartEnhancer',
    'EnhancedCard',
    'HybridParser',
    'AnkiGenerator',
    'convert_heic_to_jpeg',
    'load_image',
    'find_table_contour',
    'warp_perspective',
    'save_debug_image'
]