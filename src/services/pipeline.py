import os
from pathlib import Path
from internal.image_processing import convert_heic_to_jpeg, prepare_image
from internal.llm import VisionEnhancer
from internal.anki import AnkiGenerator
from services.storage import upload_file, download_file, get_presigned_url
from dotenv import load_dotenv

load_dotenv()

enhancer = VisionEnhancer()

def run_pipeline(file_path: str, job_id: str) -> dict:
    local_input = f"/tmp/{job_id}_input.jpg"
    output_path = Path(f"/tmp/{job_id}_output.apkg")
    s3_key = f"outputs/{job_id}_output.apkg"
    
    img_path = None
    
    try:
        download_file(file_path, local_input)
        file_path_obj = Path(local_input)
        
        img_path = convert_heic_to_jpeg(file_path_obj)
        img_path = prepare_image(img_path)
        
        cards = enhancer.extract_cards_from_image(str(img_path))
        if not cards:
            return {"status": "failed", "error": "No kanji detected or extraction failed"}
        
        anki_generator = AnkiGenerator()
        for card in cards:
            anki_generator.add_card(
                card.kanji, card.meaning, card.on_yomi, card.kun_yomi, card.example
            )
            
        success = anki_generator.save_package(output_path)
        if not success:
            return {"status": "failed", "error": "No valid notes were created for the deck."}
            
        upload_file(str(output_path), s3_key)
        url = get_presigned_url(s3_key)
        
        return {
            "status": "done",
            "output_path": str(output_path),
            "download_url": url,
            "stats": anki_generator.get_statistics()
        }
                
    except Exception as e:
        return {"status": "failed", "error": str(e)}
        
    finally:
        for p in [local_input, img_path, str(output_path)]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception as e:
                    print(f"Warning: Failed to clean up {p}: {e}")