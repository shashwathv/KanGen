# -*- coding: utf-8 -*-
from pathlib import Path

# Anki Deck Configuration
DECK_NAME = "KanGen Flashcards"
MODEL_NAME = "Kanji Model"
MODEL_ID = 2126758096
DECK_ID = 1558220604

# Model Fields
FIELDS = [
    {'name': 'Kanji'},
    {'name': 'Meaning'},
    {'name': 'On-yomi'},
    {'name': 'Kun-yomi'},
    {'name': 'Example'}
]

# Card Styling
CSS = """
.card {
    font-family: sans-serif;
    text-align: center;
    font-size: 24px;
    color: black;
    background-color: white;
}
h1 {
    font-size: 100px;
}
#answer {
    margin: 20px 0;
}
"""

# Card Templates
TEMPLATES = [
    {
        'name': 'Recognition card',
        'qfmt': '<h1>{{Kanji}}</h1>',
        'afmt': """{{FrontSide}}
        <hr id="answer">
        <div class="meaning">{{Meaning}}</div><br>
        <div class="readings">
            <b>On:</b> {{On-yomi}}<br>
            <b>Kun:</b> {{Kun-yomi}}
        </div><br>
        <div class="examples">
            <i>{{Example}}</i>
        </div>"""
    }
]

# Image Processing
MIN_CONTOUR_AREA = 50000
APPROX_POLY_EPSILON = 0.02

# Smart OCR Configuration
PROXIMITY_RADIUS = 100  # Pixels to search around kanji anchor
MIN_OCR_CONFIDENCE = 0.5  # Minimum confidence to consider OCR result
VALIDATION_CONFIDENCE_THRESHOLD = 0.7  # Threshold for valid/invalid grouping

# Kanji Unicode Range
KANJI_START = '\u4e00'
KANJI_END = '\u9fff'

# Kana Unicode Ranges
HIRAGANA_START = '\u3040'
HIRAGANA_END = '\u309f'
KATAKANA_START = '\u30a0'
KATAKANA_END = '\u30ff'