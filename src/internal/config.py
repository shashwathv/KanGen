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
@import url("_noto-sans-jp.css");

* { box-sizing: border-box; margin: 0; padding: 0; }

.card {
    font-family: "Noto Sans JP", "Hiragino Kaku Gothic ProN", "Yu Gothic", sans-serif;
    background: #FAFAF7;
    color: #1a1a1a;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    padding: 16px;
}

.card-inner {
    background: #ffffff;
    border: 1px solid #e8e4db;
    border-radius: 16px;
    padding: 32px 28px;
    max-width: 480px;
    width: 100%;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
    text-align: center;
}

/* FRONT */
.kanji-display {
    font-size: 110px;
    line-height: 1.1;
    color: #1a1a1a;
    letter-spacing: -2px;
    margin-bottom: 8px;
}

.front-hint {
    font-size: 13px;
    color: #999;
    letter-spacing: 1px;
    text-transform: uppercase;
}

/* BACK */
.divider {
    border: none;
    border-top: 1px solid #e8e4db;
    margin: 20px 0;
}

.meaning {
    font-size: 22px;
    font-weight: 600;
    color: #1a1a1a;
    margin-bottom: 18px;
}

.readings-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-bottom: 18px;
}

.reading-box {
    background: #f5f3ee;
    border-radius: 10px;
    padding: 10px 12px;
}

.reading-label {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #888;
    margin-bottom: 4px;
}

.reading-label.on  { color: #c0392b; }
.reading-label.kun { color: #2980b9; }

.reading-value {
    font-size: 20px;
    color: #1a1a1a;
    letter-spacing: 1px;
}

.reading-value.empty {
    font-size: 14px;
    color: #ccc;
    font-style: italic;
}

.example-box {
    background: #f9f7f2;
    border-left: 3px solid #c8b97a;
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
    text-align: left;
    font-size: 15px;
    color: #444;
    line-height: 1.6;
}

.example-label {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #c8b97a;
    margin-bottom: 4px;
}
"""

# Card Templates
TEMPLATES = [
    {
        'name': 'Recognition card',
        'qfmt': """
<div class="card-inner">
    <div class="kanji-display">{{Kanji}}</div>
    <div class="front-hint">What does this mean?</div>
</div>
""",
        'afmt': """
<div class="card-inner">
    <div class="kanji-display">{{Kanji}}</div>
    <hr class="divider">
    <div class="meaning">{{Meaning}}</div>

    <div class="readings-grid">
        <div class="reading-box">
            <div class="reading-label on">▶ On-yomi</div>
            {{#On-yomi}}
            <div class="reading-value">{{On-yomi}}</div>
            {{/On-yomi}}
            {{^On-yomi}}
            <div class="reading-value empty">—</div>
            {{/On-yomi}}
        </div>
        <div class="reading-box">
            <div class="reading-label kun">▷ Kun-yomi</div>
            {{#Kun-yomi}}
            <div class="reading-value">{{Kun-yomi}}</div>
            {{/Kun-yomi}}
            {{^Kun-yomi}}
            <div class="reading-value empty">—</div>
            {{/Kun-yomi}}
        </div>
    </div>

    {{#Example}}
    <div class="example-box">
        <div class="example-label">Example</div>
        {{Example}}
    </div>
    {{/Example}}
</div>
"""
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