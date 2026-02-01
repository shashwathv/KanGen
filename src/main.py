# -*- coding: utf-8 -*-
import os
import sys
import click
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv

# Ensure kangen package is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from kangen.image_processing import (
    convert_heic_to_jpeg, 
    load_image, 
    find_table_contour, 
    warp_perspective,
    save_debug_image
)
from kangen.ocr import SmartOCRService
from kangen.grouper import KanjiGrouper
from kangen.llm import SmartEnhancer
from kangen.anki import AnkiGenerator

# Load environment variables from .env file
load_dotenv()

@click.command()
@click.argument('input_paths', nargs=-1, type=click.Path(exists=True))
@click.option('--output', '-o', default='output_deck.apkg', help='Output path for the Anki deck file.')
@click.option('--gpu/--no-gpu', default=False, help='Use GPU for OCR (requires CUDA).')
@click.option('--api-key', envvar='GEMINI_API_KEY', help='Google Gemini API Key (or set GEMINI_API_KEY env var).')
@click.option('--debug-images', is_flag=True, help='Save debug images (blobs, contours).')
@click.option('--no-warp', is_flag=True, help='Skip perspective correction (process image as-is).')
@click.option('--proximity', default=100, help='Proximity radius for grouping text (pixels).')
def main(input_paths, output, gpu, api_key, debug_images, no_warp, proximity):
    """
    KanGen: Generate Anki Flashcards from Kanji Images.
    
    New Smart Architecture - Layout Agnostic!
    - Extracts all text without column assumptions
    - Groups kanji with nearby text by proximity
    - Validates readings using dictionary
    - Self-correcting with AI enhancement
    
    INPUT_PATHS: One or more paths to images (JPEG, PNG, HEIC) or directories.
    """
    if not input_paths:
        click.echo("❌ Please provide at least one image path.")
        return

    # Expand directories
    expanded_paths = []
    for p in input_paths:
        path = Path(p).resolve()
        if not path.exists():
            click.echo(f"⚠️ Path does not exist: {path}")
            continue
            
        if path.is_dir():
            expanded_paths.extend(list(path.glob('*')))
        else:
            expanded_paths.append(path)
            
    # Filter valid extensions
    valid_exts = {'.jpg', '.jpeg', '.png', '.heic', '.heif'}
    source_files = [p for p in expanded_paths if p.suffix.lower() in valid_exts]
    
    if not source_files:
        click.echo("❌ No valid image files found.")
        return

    click.echo(f"📸 Processing {len(source_files)} file(s)...")
    
    # Validate output path
    output_path = Path(output)
    if output_path.exists():
        if not click.confirm(f"⚠️ {output_path} already exists. Overwrite?"):
            return

    # Create debug directory if needed
    if debug_images:
        debug_dir = Path('debug_output')
        debug_dir.mkdir(exist_ok=True)
        click.echo(f"🔍 Debug images will be saved to {debug_dir}")

    # Initialize Services
    click.echo("🔧 Initializing services...")
    
    try:
        ocr_service = SmartOCRService(use_gpu=gpu)
    except Exception as e:
        click.echo(f"❌ Failed to initialize OCR: {e}", err=True)
        click.echo("💡 Hint: Try running with --no-gpu or check EasyOCR installation")
        return
    
    try:
        grouper = KanjiGrouper(proximity_radius=proximity)
        enhancer = SmartEnhancer(api_key=api_key)
        anki_generator = AnkiGenerator()
    except Exception as e:
        click.echo(f"❌ Failed to initialize services: {e}", err=True)
        return
    
    if not api_key:
        click.echo("⚠️ No GEMINI_API_KEY found. Using fallback mode (may be less accurate).")

    # Process each image
    total_kanji_found = 0
    total_cards_created = 0
    
    for file_path in tqdm(source_files, desc="Processing Images"):
        try:
            # Step 1: Image Preprocessing
            img_path = convert_heic_to_jpeg(file_path)
            original_img = load_image(img_path)
            
            # Optional: Perspective correction for tables
            if not no_warp:
                table_contour = find_table_contour(original_img)
                if table_contour is not None:
                    processed_img = warp_perspective(original_img, table_contour)
                    
                    if debug_images:
                        save_debug_image(
                            original_img, 
                            debug_dir / f"{file_path.stem}_contour.png",
                            table_contour
                        )
                else:
                    processed_img = original_img
                    tqdm.write(f"⚠️ No table contour found in {file_path.name}, using full image")
            else:
                processed_img = original_img
            
            if debug_images:
                save_debug_image(
                    processed_img,
                    debug_dir / f"{file_path.stem}_processed.png"
                )
            
            # Step 2: Smart OCR - Extract all text with context
            text_blocks = ocr_service.extract_all_text_with_context(processed_img)
            
            if not text_blocks:
                tqdm.write(f"⚠️ No text detected in {file_path.name}")
                continue
            
            tqdm.write(f"📝 Detected {len(text_blocks)} text blocks in {file_path.name}")
            
            # Step 3: Group by proximity
            kanji_entries = grouper.group_by_proximity(text_blocks)
            
            if not kanji_entries:
                tqdm.write(f"⚠️ No kanji entries found in {file_path.name}")
                continue
            
            total_kanji_found += len(kanji_entries)
            tqdm.write(f"🎯 Found {len(kanji_entries)} kanji entries in {file_path.name}")
            
            # Step 4: Enhance and add to deck
            for entry in kanji_entries:
                try:
                    # Enhance with validation-based routing
                    enhanced_card = enhancer.enhance(entry)
                    
                    if enhanced_card:
                        # Add to Anki deck
                        success = anki_generator.add_card(
                            enhanced_card.kanji,
                            enhanced_card.meaning,
                            enhanced_card.on_yomi,
                            enhanced_card.kun_yomi,
                            enhanced_card.example
                        )
                        
                        if success:
                            total_cards_created += 1
                    else:
                        tqdm.write(f"⚠️ Could not enhance '{entry.kanji}'")
                        
                except Exception as e:
                    tqdm.write(f"❌ Error processing '{entry.kanji}': {e}")

        except Exception as e:
            tqdm.write(f"❌ Failed to process {file_path.name}: {e}")

    # Step 5: Save Deck
    click.echo("\n" + "="*60)
    click.echo("📊 Processing Summary:")
    click.echo(f"   Images processed: {len(source_files)}")
    click.echo(f"   Kanji entries found: {total_kanji_found}")
    
    stats = anki_generator.get_statistics()
    click.echo(f"   Cards created: {stats['created']}")
    click.echo(f"   Cards skipped: {stats['skipped']}")
    click.echo("="*60)
    
    if anki_generator.save_package(output_path):
        click.echo(f"\n✅ Success! Deck saved to: {output_path}")
    else:
        click.echo(f"\n❌ Failed to save deck")

if __name__ == '__main__':
    main()
