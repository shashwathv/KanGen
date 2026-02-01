# KanGen: AI-Powered Anki Flashcard Generator

KanGen (Kanji Generator) is a robust tool designed to automate the creation of Anki flashcards from physical study materials (textbooks, worksheets). It uses Computer Vision to detect tables and AI to understand and restructure the content.

## 🚀 Key Features

-   **Intelligent Image Processing**: Automatically finds tables in images, corrects perspective (de-skewing), and converts HEIC/HEIF photos to compatible formats.
-   **AI-Powered Data Cleaning (Gemini 2.5)**:
    -   **Context Awareness**: Distinguishes between *On-yomi* (Katakana) and *Kun-yomi* (Hiragana).
    -   **Auto-Correction**: Fixes common OCR errors.
    -   **Data Enrichment**: Generates missing meanings or example sentences.
-   **Robust Fallback**: Automatically switches to a Regex/Sudachi-based parser if the AI service is unavailable.
-   **Anki Integration**: Generates `.apkg` files ready to import directly into Anki.

## 📦 Install Usage

Prerequisites: Python 3.9+

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd KanGen
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Setup API Key** (Optional but Recommended):
    -   Get a key from [Google AI Studio](https://aistudio.google.com/).
    -   Create a `.env` file in the project root:
        ```bash
        GEMINI_API_KEY=your_key_here
        ```

## 💻 Usage

Run the tool directy via python:

```bash
# Process a single image
python src/main.py photos/page1.jpg -o chapter1.apkg

# Process a folder of images
python src/main.py photos/ -o complete_deck.apkg
```

### Options

-   `--output`, `-o`: Output path for the .apkg file (default: output_deck.apkg).
-   `--gpu`: Use GPU for OCR (requires CUDA).
-   `--no-warp`: Skip perspective correction (process image as-is).
-   `--debug-images`: Save debug images (contours, processed blobs) to `debug_output/`.
-   `--api-key`: Explicitly pass the Gemini API key (overrides .env).

## 🧠 Logic Flow

1.  **Input**: Image is loaded (HEIC converted to JPEG if needed).
2.  **Vision**: The main table is detected and cropped.
3.  **OCR**: Text is extracted using EasyOCR.
4.  **Grouping**: Text blocks are grouped into logical entries based on spatial proximity.
5.  **Parsing/Enhancement**:
    -   **AI Mode**: Queries Google Gemini to clean and structure the data.
    -   **Legacy Mode**: Uses SudachiPy and Regex to split text if AI is unavailable.
6.  **Generation**: Anki Notes are created and packaged into an `.apkg` file.
