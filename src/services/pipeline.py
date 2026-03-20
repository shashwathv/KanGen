from internal.image_processing import convert_heic_to_jpeg, load_image, find_table_contour, warp_perspective
from internal.ocr import SmartOCRService
from internal.grouper import KanjiGrouper
from internal.llm import SmartEnhancer
from internal.anki import AnkiGenerator
from services.storage import upload_file, download_file, get_presigned_url
import os
from dotenv import load_dotenv
load_dotenv()
from pathlib import Path

ocr_service = SmartOCRService(use_gpu=False)
grouper = KanjiGrouper()
enhancer = SmartEnhancer(api_key=os.getenv("GEMINI_API_KEY"))

def run_pipeline(file_path: str, job_id: str) -> dict:
    local_input = f"/tmp/{job_id}_input.jpg"
    download_file(file_path, local_input)
    print(f"DEBUG: S3 key received: {file_path}")
    print(f"DEBUG: Local input path: {local_input}")
    print(f"DEBUG: File exists after download: {os.path.exists(local_input)}")
    file_path = Path(local_input)
    anki_generator = AnkiGenerator()
    try:
        img_path = convert_heic_to_jpeg(file_path)
        original_img = load_image(img_path)

        table_contour = find_table_contour(original_img)
        if table_contour is not None:
            processed_img = warp_perspective(original_img, table_contour)
        else:
            processed_img = original_img
        
        text_blocks = ocr_service.extract_all_text_with_context(processed_img)
        if not text_blocks:
                return {"status": "failed", "error": "No text detected"}
        
        kanji_entries = grouper.group_by_proximity(text_blocks)
        if not kanji_entries:
                return {"status":"failed", "error":f"⚠️ No kanji found in {file_path}"}

        try:
            enhanced_cards = enhancer.enhance_all(kanji_entries)
        except Exception as e:
                enhanced_cards = []
        for enhanced_card in enhanced_cards:
                try:
                    success = anki_generator.add_card(
                        enhanced_card.kanji,
                        enhanced_card.meaning,
                        enhanced_card.on_yomi,
                        enhanced_card.kun_yomi,
                        enhanced_card.example
                    )
                except Exception as e:
                    continue
        
        output_path = Path(f"/tmp/{job_id}_output.apkg")
        anki_generator.save_package(output_path)
        s3_key = f"outputs/{job_id}_output.apkg"
        upload_file(str(output_path), s3_key)
        url = get_presigned_url(s3_key)
        return {
            "status": "done",
            "output_path": output_path,
            "download_url":url,
            "stats": anki_generator.get_statistics()
        }
                
    except Exception as e:
        return {"status": "failed", "error": str(e)}