from pathlib import Path
from PIL import Image 
from pillow_heif import register_heif_opener

register_heif_opener()

def convert_heic_to_jpeg(heic_path: Path) -> Path:
    if heic_path.suffix.lower() not in ['.heic', '.heif']:
        return heic_path
    
    jpeg_path = heic_path.with_suffix('.jpg')
    if jpeg_path.exists():
        return jpeg_path

    try:
        with Image.open(heic_path) as image:
            image.convert("RGB").save(jpeg_path, "JPEG")
        return jpeg_path
    except Exception as e:
        raise ValueError(f"Failed to convert HEIC to JPEG: {e}")