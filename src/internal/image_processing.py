from pathlib import Path
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

register_heif_opener()

MAX_EDGE = 1600
JPEG_QUALITY = 88


def convert_heic_to_jpeg(heic_path: Path) -> Path:
    """Convert HEIC/HEIF to JPEG on disk. Non-HEIC inputs returned untouched."""
    if heic_path.suffix.lower() not in ['.heic', '.heif']:
        return heic_path

    jpeg_path = heic_path.with_suffix('.jpg')
    if jpeg_path.exists():
        return jpeg_path

    try:
        with Image.open(heic_path) as image:
            image.convert("RGB").save(jpeg_path, "JPEG", quality=JPEG_QUALITY)
        return jpeg_path
    except Exception as e:
        raise ValueError(f"Failed to convert HEIC to JPEG: {e}")


def prepare_image(image_path: Path) -> Path:
    try:
        with Image.open(image_path) as img:
            img = ImageOps.exif_transpose(img)
            img = img.convert("RGB")

            w, h = img.size
            longest = max(w, h)
            if longest > MAX_EDGE:
                scale = MAX_EDGE / longest
                img = img.resize((round(w * scale), round(h * scale)), Image.LANCZOS)

            img.save(image_path, "JPEG", quality=JPEG_QUALITY)
        return image_path
    except Exception as e:
        print(f"Warning: image prep failed for {image_path}, using original: {e}")
        return image_path