import os
from pathlib import Path
from internal.image_processing import convert_heic_to_jpeg, prepare_image
from internal.llm import VisionEnhancer
from services.storage import download_file
from dotenv import load_dotenv

load_dotenv()

enhancer = VisionEnhancer()

def run_pipeline(file_path: str, job_id: str) -> dict:
    local_input = f"/tmp/{job_id}_input.jpg"
    img_path = None
    try:
        download_file(file_path, local_input)
        img_path = convert_heic_to_jpeg(Path(local_input))
        img_path = prepare_image(img_path)

        cards = enhancer.extract_cards_from_image(str(img_path))
        if not cards:
            return {"status": "failed", "error": "No kanji detected or extraction failed"}

        return {
            "status": "done",
            "cards": [c.model_dump() for c in cards],  
        }
    except Exception as e:
        return {"status": "failed", "error": str(e)}
    finally:
        for p in [local_input, img_path]:
            if p and os.path.exists(str(p)):
                try:
                    os.remove(p)
                except Exception:
                    pass