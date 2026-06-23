# -*- coding: utf-8 -*-
import genanki #type: ignore
import logging
from pathlib import Path
from typing import List, Dict, Optional
from internal.config import DECK_ID, DECK_NAME, MODEL_ID, MODEL_NAME, FIELDS, TEMPLATES, CSS

logger = logging.getLogger(__name__)

class AnkiGenerator:
    def __init__(self, deck_name: str = DECK_NAME, deck_id: int = DECK_ID):
        self.deck_id = deck_id
        self.deck_name = deck_name
        
        self.model = genanki.Model(
            MODEL_ID,
            MODEL_NAME,
            fields=FIELDS,
            templates=TEMPLATES,
            css=CSS
        )
        
        self.deck = genanki.Deck(self.deck_id, self.deck_name)
        self.notes_created = 0
        self.notes_skipped = 0
        self.seen_kanji = set()  # Track duplicates

    def add_card(self, kanji: str, meaning: str, on_yomi: str, kun_yomi: str, example: str) -> bool:

        # Validation 1: Must have kanji and meaning at minimum
        if not kanji or not kanji.strip():
            logger.warning("Skipping card: No kanji provided")
            self.notes_skipped += 1
            return False
        
        if not meaning or not meaning.strip():
            logger.warning("Skipping card for %s: No meaning provided", kanji)
            self.notes_skipped += 1
            return False
        
        # Validation 2: Check for duplicates
        kanji_key = kanji.strip()
        if kanji_key in self.seen_kanji:
            logger.warning("Skipping duplicate kanji: '%s'", kanji_key)
            self.notes_skipped += 1
            return False
        
        # Create the note
        note = genanki.Note(
            model=self.model,
            fields=[
                kanji.strip(),
                meaning.strip(),
                on_yomi.strip() if on_yomi else '',
                kun_yomi.strip() if kun_yomi else '',
                example.strip() if example else ''
            ]
        )
        
        self.deck.add_note(note)
        self.seen_kanji.add(kanji_key)
        self.notes_created += 1
        return True

    def save_package(self, output_path: Path) -> bool:
        if self.notes_created == 0:
            logger.error("No notes were added to the deck.")
            return False
        
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            genanki.Package(self.deck).write_to_file(str(output_path))
            logger.info("Saved Anki deck to: %s", output_path)
            logger.info("Created: %d cards.", self.notes_created)
            if self.notes_skipped > 0:
                logger.info("Skipped: %d cards", self.notes_skipped)
            return True
            
        except Exception as e:
            logger.error("Failed to save deck: %s", e)
            return False
    
    def get_statistics(self) -> Dict[str, int]:
        return {
            'created': self.notes_created,
            'skipped': self.notes_skipped,
            'total_processed': self.notes_created + self.notes_skipped
        }