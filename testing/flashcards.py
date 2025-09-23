import cv2 as cv
import numpy as np
import pytesseract as pyt
from PIL import Image
from pillow_heif import register_heif_opener
from io import BytesIO
import genanki
from sudachipy import Tokenizer, Dictionary
from jamdict import Jamdict
from pathlib import Path

#CONSTANTS AND VARIABLES
register_heif_opener()
INPUT_IMG_PATH = "/home/guts/Projects/anki_flashcards/test.heic"
OUTPUT_DECK_PATH = "/home/guts/Projects/anki_flashcards/output_deck.apkg"
DECK_NAME = "Kanji Flashcards"
MODEL_ID = 2126758096
DECK_ID = 1558220604

jam = Jamdict()
tokenizer_obj = Dictionary().create()

#genanki.Model structure for the flashcards
my_fields = [
    {'name': 'Kanji'},
    {'name': 'Meaning'},
    {'name': 'On-yomi'},
    {'name': 'Kun-yomi'},
    {'name': 'Example'}
]

my_css = """
.card {
    font-family: sans-serif;
    text-align: center;
    font-size: 24px;
    color: black;
    background-color: white;
}

h1 {
    font-size: 100px;}
}
"""

my_template = [
    {
        'name': 'Recognition card',
        'qfmt': '<h1>{{Kanji}}</h1>',
        'afmt': '{{FrontSide}}<hr id="answer">{{Meaning}}<br><br><b>On:</b> {{On-yomi}}<br><b>Kun:</b> {{Kun-yomi}}<br><br><i>{{Example}}</i>'
    }
]

#Final model for the flashcards
my_kanji_model = genanki.Model(
    MODEL_ID,
    'Kanji Model',
    fields=my_fields,
    templates=my_template,
    css=my_css
)

list_of_cards = []


def main():
    _, ext = INPUT_IMG_PATH.split('.')
    formats = ['jpeg', 'jpg', 'png']
    source_path = Path(INPUT_IMG_PATH)

    if ext.lower() in formats:
        img_path = INPUT_IMG_PATH
    elif ext.lower() == 'heic':
        img_path = source_path.with_suffix('.jpeg')
        convert_to_jpeg(INPUT_IMG_PATH, img_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    img = cv.imread(str(img_path))
    if img is None:
        raise ValueError(f"Could not read image from {img_path}")

    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    # Detect lines from the preprocessed, resized image
    y_coords, x_coords, v_lines_raw = find_grid_lines(img)
    print(f"Found {len(y_coords)} horizontal lines at y-coordinates: {y_coords}")
    print(f"Found {len(x_coords)} vertical lines at x-coordinates: {x_coords}")
    

    preprocessed = img.copy()
    # Draw horizontal lines (green)
    for y in y_coords:
        cv.line(preprocessed, (0, int(y)), (preprocessed.shape[1], int(y)), (0, 255, 0), 1)
    # Draw vertical lines (blue)
    for x in x_coords:
        cv.line(preprocessed, (int(x), 0), (int(x), preprocessed.shape[0]), (255, 0, 0), 1)
    window_name = "Grid Overlay"
    cv.namedWindow(window_name, cv.WINDOW_NORMAL)
    cv.imshow(window_name, preprocessed)
    cv.waitKey(0)

    

    for i in range(len(y_coords) - 1):
        y_start = int(y_coords[i])
        y_end = int(y_coords[i + 1])

        if i in range(len(y_coords) -1):
            y_start = int(y_coords[i])
            y_end = int(y_coords[i + 1])
        
        if y_end - y_start < 20:
            continue

        row_x_coords = find_cols(v_lines_raw, y_start, y_end)

        if len(row_x_coords) < 2:
            continue

        kanji_col_start = int(row_x_coords[0])
        kanji_col_end = int(row_x_coords[1])
        info_col_start = int(row_x_coords[1])
        info_col_end = int(row_x_coords[-1])

        padding = 5
        kanji_cell = gray[y_start + padding : y_end - padding, kanji_col_start + padding : kanji_col_end - padding]
        info_cell = gray[y_start + padding : y_end - padding, info_col_start + padding : info_col_end - padding]

        if kanji_cell.size == 0 or info_cell.size == 0:
            continue

        cv.imshow('Kanji Cell', kanji_cell)
        cv.imshow('Info Cell', info_cell)
        cv.waitKey(0)

        kanji_text = pyt.image_to_string(kanji_cell,   lang='jpn', config='--psm 10').strip()
        info_text = pyt.image_to_string(info_cell, lang='jpn+eng', config='--psm 6').strip()

        print(f"--- Row {i + 1} ---")
        print(f"Kanji found: {kanji_text}")
        print(f"Info found: {info_text}")   
        print('\n')


def resize(frame, scale=0.2):
    """
    Resizes the image frame
    """
    width = int(frame.shape[1] * scale)
    height = int(frame.shape[0] * scale)
    dimensions = (width, height)
    return cv.resize(frame, dimensions, interpolation=cv.INTER_AREA)


def convert_to_jpeg(other_path, jpeg_path):
    """
    Converts an image to JPEG format.
    """
    image = Image.open(other_path)
    image = image.convert("RGB")
    image.save(jpeg_path, "JPEG")


def pre_processing(img):
    """
    Processes the image using opencv
    """
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    blurred = cv.GaussianBlur(gray, (3,3), 0)
    thresh = cv.adaptiveThreshold(blurred, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY_INV, 15, 10)
    return thresh


def merge_close_coords(coords, threshold=10):
    """Merges coordinates that are within a threshold of each other"""
    if not coords:
        return []
    coords.sort()
    merged = [coords[0]]
    for coord in coords[1:]:
        if abs(coord - merged[-1]) > threshold:
            merged.append(coord)
    return merged

def find_grid_lines(img):
    # Make sure image is grayscale
    if len(img.shape) == 3:
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    else:
        gray = img.copy()

    # Binary inverse thresholding
    _, binary = cv.threshold(gray, 0, 255, cv.THRESH_BINARY_INV + cv.THRESH_OTSU)

    # # --- Horizontal lines ---
    horizontal_kernel = cv.getStructuringElement(cv.MORPH_RECT, (gray.shape[1] // 30, 2))
    detected_horizontal = cv.morphologyEx(binary, cv.MORPH_OPEN, horizontal_kernel, iterations=2)
    contours_h, _ = cv.findContours(detected_horizontal, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    y_coords = [cv.boundingRect(c)[1] for c in contours_h]

    # --- Vertical lines ---
    vertical_kernel = cv.getStructuringElement(cv.MORPH_RECT, (1, gray.shape[0] // 30))
    detected_vertical = cv.morphologyEx(binary, cv.MORPH_OPEN, vertical_kernel, iterations=2)
    contours_v, _ = cv.findContours(detected_vertical, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    
    vertical_lines_raw = [cv.boundingRect(c) for c in contours_v]
    x_coords = [x for x, y, w, h in vertical_lines_raw]

    # Merge coordinates for a clean list
    unique_y_coords = merge_close_coords(y_coords, threshold=15)
    unique_x_coords = merge_close_coords(x_coords, threshold=15)

    return unique_y_coords, unique_x_coords, vertical_lines_raw


def find_cols(v_lines_raw, y_start, y_end):
    """Finds the x-coordinates of vertical lines that intersect a given row."""
    cols_in_row = []
    for x, y, w, h in v_lines_raw:
        if y < y_end and (y + h) > y_start:
            cols_in_row.append(x)
    return sorted(cols_in_row)

if __name__ == "__main__":
    main()
