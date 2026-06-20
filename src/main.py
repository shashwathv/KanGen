# -*- coding: utf-8 -*-
import os
import sys
import click
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from internal.image_processing import convert_heic_to_jpeg, prepare_image
from internal.llm import VisionEnhancer
from internal.anki import AnkiGenerator

load_dotenv()

@click.command()
@click.argument('input_paths', nargs=-1, type=click.Path(exists=True))
@click.option('--output', '-o', default='output_deck.apkg', help='Output path for the Anki deck file.')
@click.option('--api-key', envvar='GEMINI_API_KEY', help='Google Gemini API Key.')
def main(input_paths, output, api_key):
    """KanGen: Generate Anki Flashcards directly from images using Gemini Vision."""
    if not input_paths:
        click.echo("❌ Please provide at least one image path.")
        return

    expanded_paths = []
    for p in input_paths:
        path = Path(p).resolve()
        if path.is_dir():
            expanded_paths.extend(list(path.glob('*')))
        else:
            expanded_paths.append(path)

    valid_exts = {'.jpg', '.jpeg', '.png', '.heic', '.heif'}
    source_files = [p for p in expanded_paths if p.suffix.lower() in valid_exts]

    if not source_files:
        click.echo("❌ No valid image files found.")
        return

    output_path = Path(output)
    if output_path.exists() and not click.confirm(f"⚠️ {output_path} already exists. Overwrite?"):
        return

    try:
        enhancer = VisionEnhancer(api_key=api_key)
        anki_generator = AnkiGenerator()
    except Exception as e:
        click.echo(f"❌ Failed to initialize Gemini Vision: {e}", err=True)
        return

    total_cards_created = 0

    for file_path in tqdm(source_files, desc="Processing Images"):
        try:
            img_path = convert_heic_to_jpeg(file_path)
            img_path = prepare_image(img_path)
            
            cards = enhancer.extract_cards_from_image(str(img_path))
            if not cards:
                tqdm.write(f"⚠️ No kanji found in {file_path.name}")
                continue

            for card in cards:
                success = anki_generator.add_card(
                    card.kanji, card.meaning, card.on_yomi, card.kun_yomi, card.example
                )
                if success: total_cards_created += 1

        except Exception as e:
            tqdm.write(f"❌ Failed to process {file_path.name}: {e}")

    click.echo("\n" + "="*60)
    click.echo("📊 Processing Summary:")
    stats = anki_generator.get_statistics()
    click.echo(f"   Images processed: {len(source_files)}")
    click.echo(f"   Cards created: {stats['created']}")
    click.echo(f"   Cards skipped: {stats['skipped']}")
    click.echo("="*60)

    if anki_generator.save_package(output_path):
        click.echo(f"\n✅ Success! Deck saved to: {output_path}")
    else:
        click.echo(f"\n❌ Failed to save deck. No valid cards were generated.")

if __name__ == '__main__':
    main()