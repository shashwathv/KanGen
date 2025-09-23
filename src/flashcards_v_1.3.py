import cv2 as cv
import numpy as np
import easyocr
from PIL import Image
from pillow_heif import register_heif_opener
from pathlib import Path
import genanki
from sudachipy import Dictionary, Tokenizer
import re

# --- 1. SETUP AND CONSTANTS ---
register_heif_opener()
OUTPUT_DECK_PATH = "output_deck.apkg"
DECK_NAME = "Kanji Flashcards"
MODEL_ID = 2126758096
DECK_ID = 1558220604

# Initialize SudachiPy Tokenizer
tokenizer_obj = Dictionary().create()

# Your Genanki model setup
my_fields = [{'name': 'Kanji'}, {'name': 'Meaning'}, {'name': 'On-yomi'}, {'name': 'Kun-yomi'}, {'name': 'Example'}]
my_css = ".card {font-family: sans-serif; text-align: center; font-size: 24px; color: black; background-color: white;} h1 {font-size: 100px;}"
my_template = [{'name': 'Recognition card', 'qfmt': '<h1>{{Kanji}}</h1>', 'afmt': '{{FrontSide}}<hr id="answer">{{Meaning}}<br><br><b>On:</b> {{On-yomi}}<br><b>Kun:</b> {{Kun-yomi}}<br><br><i>{{Example}}</i>'}]
my_kanji_model = genanki.Model(MODEL_ID, 'Kanji Model', fields=my_fields, templates=my_template, css=my_css)
list_of_cards = []

# --- 2. HELPER FUNCTIONS ---

def convert_to_jpeg(heic_path, jpeg_path):
    """Converts HEIC images to JPEG."""
    with Image.open(heic_path) as image:
        image.convert("RGB").save(jpeg_path, "JPEG")

def create_content_blobs(image):
    """Creates a binary 'blob' image to find the main table contour."""
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    inverted_gray = cv.bitwise_not(gray)
    _ , binary = cv.threshold(inverted_gray, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
    kernel = cv.getStructuringElement(cv.MORPH_RECT, (10, 3))
    dilated = cv.dilate(binary, kernel, iterations=3)
    return dilated

def find_table_contour(image):
    """Finds the largest rectangular contour, assumed to be the table."""
    blob_image = create_content_blobs(image)
    contours, _ = cv.findContours(blob_image, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    table_contour = None
    if contours:
        contours = sorted(contours, key=cv.contourArea, reverse=True)
        for contour in contours:
            if cv.contourArea(contour) < 50000:
                continue
            peri = cv.arcLength(contour, True)
            approx = cv.approxPolyDP(contour, 0.02 * peri, True)
            if len(approx) == 4:
                table_contour = approx
                break
    return table_contour

def order_points(pts):
    """Sorts the 4 points of a contour into a consistent order."""
    pts = pts.reshape(4, 2)
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def warp_perspective(image, contour):
    """Applies a perspective transform to get a top-down view of the table."""
    ordered_contour = order_points(contour)
    (tl, tr, br, bl) = ordered_contour
    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    new_width = max(int(widthA), int(widthB))
    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    new_height = max(int(heightA), int(heightB))
    destination_points = np.array([[0, 0], [new_width - 1, 0], [new_width - 1, new_height - 1], [0, new_height - 1]], dtype="float32")
    matrix = cv.getPerspectiveTransform(ordered_contour, destination_points)
    warped_image = cv.warpPerspective(image, matrix, (new_width, new_height))
    return warped_image
    
def parse_info_text(text_block, tokenizer):
    """
    Parses a block of text using SudachiPy to extract flashcard fields.
    """
    meaning_list = []
    on_yomi_list = []
    kun_yomi_list = []
    
    cleaned_text = re.sub(r'\(.*?\)', '', text_block)
    morphemes = tokenizer.tokenize(cleaned_text)
    
    for m in morphemes:
        part_of_speech = m.part_of_speech()
        if m.surface().isascii() and "Symbol" not in part_of_speech[0]:
            meaning_list.append(m.surface())
        if not m.surface().isascii() and "Symbol" not in part_of_speech[0]:
            if "Noun" in part_of_speech[0] and len(re.findall(r'[\u4e00-\u9faf]', m.surface())) >= 2:
                on_yomi_list.append(f"{m.surface()}({m.reading_form()})")
            else:
                reading_hira = "".join([chr(ord(c) - 96) for c in m.reading_form() if 'A' <= c <= 'Z'])
                kun_yomi_list.append(f"{m.surface()}({reading_hira})")

    meaning = " ".join(dict.fromkeys(meaning_list))
    on_yomi = " ".join(dict.fromkeys(on_yomi_list))
    kun_yomi = " ".join(dict.fromkeys(kun_yomi_list))
    example = " ".join(text_block.split())
    return meaning, on_yomi, kun_yomi, example

def is_single_kanji(text):
    """Checks if a string is a single Japanese Kanji character."""
    return bool(re.fullmatch(r'[\u4e00-\u9fff]', text))

def assign_to_columns(ocr_results, table_width):
    """Assigns all detected text into three columns based on horizontal position."""
    col_centers = [table_width * 0.15, table_width * 0.45, table_width * 0.75]
    columns = [[], [], []]
    for (bbox, text, prob) in ocr_results:
        x_center = (bbox[0][0] + bbox[1][0]) / 2
        y_center = (bbox[0][1] + bbox[2][1]) / 2
        col_index = int(np.argmin([abs(x_center - center) for center in col_centers]))
        columns[col_index].append({'text': text, 'y': y_center})
    for col in columns:
        col.sort(key=lambda item: item['y'])
    return columns

# --- 3. MAIN EXECUTION ---
def main():
    # --- STAGE A: FIND AND ISOLATE THE TABLE ---
    input_path = Path(input("Enter your image/s path (seperate with commas for multiple files): "))
    source_paths = [Path(p.strip()) for p in input_path.split(',')]
    print(f"Processing {(len(source_paths))} file(s)....")
    reader = easyocr.Reader(['ja', 'en'], gpu=True)
    print("Initializing EasyOCR... (this can be slow on first run)")
    for path in source_paths:
        print(f"Processing {path} ")
        if input_path.suffix.lower() == '.heic':
            img_path = input_path.with_suffix('.jpeg')
            convert_to_jpeg(input_path, img_path)
        else:
            img_path = str(input_path)

        img = cv.imread(str(img_path))
        if img is None:
            raise ValueError(f"Could not read image from {img_path}")
        
        table_contour = find_table_contour(img)
        if table_contour is None:
            print("No table contour was found.")
            return

        warped_table = warp_perspective(img, table_contour)
        
        # --- STAGE B: EXTRACT ALL TEXT BLOCKS WITH EASYOCR ---
        results = reader.readtext(warped_table, detail=1)

        if not results:
            print("No text detected by EasyOCR.")
            return

        # --- STAGE C: PARSE AND GROUP RESULTS INTO COLUMNS ---
        table_width = warped_table.shape[1]
        columns = assign_to_columns(results, table_width)
        kanji_col, readings_col, examples_col = columns[0], columns[1], columns[2]

        # --- STAGE D: PROCESS, CREATE NOTES, AND GENERATE DECK ---
        main_kanji_entries = [item for item in kanji_col if is_single_kanji(item['text'])]
        print(f"\nSuccessfully identified {len(main_kanji_entries)} main Kanji entries. Creating Anki notes...\n")

        for i in range(len(main_kanji_entries)):
            current_kanji = main_kanji_entries[i]
            
            row_y_start = current_kanji['y'] - 20
            row_y_end = main_kanji_entries[i+1]['y'] - 20 if i + 1 < len(main_kanji_entries) else warped_table.shape[0]

            readings_text = " ".join([item['text'] for item in readings_col if row_y_start <= item['y'] < row_y_end])
            examples_text = " ".join([item['text'] for item in examples_col if row_y_start <= item['y'] < row_y_end])
            
            # Combine all text for the SudachiPy parser
            full_info_text = f"{readings_text} {examples_text}"
            
            meaning, on_yomi, kun_yomi, example = parse_info_text(full_info_text, tokenizer_obj)
            
            # Create the Anki Note
            note = genanki.Note(
                model=my_kanji_model,
                fields=[current_kanji['text'], meaning, on_yomi, kun_yomi, example]
            )
            list_of_cards.append(note)
            print(f"Created note for: {current_kanji['text']}")

    # --- STAGE E: SAVE THE ANKI DECK FILE ---
    if list_of_cards:
        deck = genanki.Deck(DECK_ID, DECK_NAME)
        for note in list_of_cards:
            deck.add_note(note)
        genanki.Package(deck).write_to_file(OUTPUT_DECK_PATH)
        print(f"\n🎉 Successfully created Anki deck with {len(list_of_cards)} cards at: {OUTPUT_DECK_PATH}")
    else:
        print("\n⚠️ No cards were created. Please check your input images.")

        
if __name__ == "__main__":
    main()