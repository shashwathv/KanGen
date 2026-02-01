# -*- coding: utf-8 -*-
import genanki #type: ignore
from pathlib import Path
from typing import List, Dict, Optional
from kangen.config import DECK_ID, DECK_NAME, MODEL_ID, MODEL_NAME, FIELDS, TEMPLATES, CSS

class AnkiGenerator:
    """Generates Anki deck packages with validation."""
    
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
        """
        Adds a single card note to the deck with validation.
        
        Returns:
            True if card was added, False if skipped
        """
        # Validation 1: Must have kanji and meaning at minimum
        if not kanji or not kanji.strip():
            print(f"⚠️ Skipping card: No kanji provided")
            self.notes_skipped += 1
            return False
        
        if not meaning or not meaning.strip():
            print(f"⚠️ Skipping card for '{kanji}': No meaning provided")
            self.notes_skipped += 1
            return False
        
        # Validation 2: Check for duplicates
        kanji_key = kanji.strip()
        if kanji_key in self.seen_kanji:
            print(f"⚠️ Skipping duplicate kanji: '{kanji_key}'")
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
        """
        Generates the .apkg file.
        
        Returns:
            True if saved successfully, False otherwise
        """
        if self.notes_created == 0:
            print("⚠️ Warning: No notes were added to the deck.")
            return False
        
        try:
            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate package
            genanki.Package(self.deck).write_to_file(str(output_path))
            print(f"✅ Saved Anki deck to {output_path}")
            print(f"   Created: {self.notes_created} cards")
            if self.notes_skipped > 0:
                print(f"   Skipped: {self.notes_skipped} cards")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save deck: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, int]:
        """Get statistics about deck creation."""
        return {
            'created': self.notes_created,
            'skipped': self.notes_skipped,
            'total_processed': self.notes_created + self.notes_skipped
        }