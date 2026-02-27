# 漢 KanGen

### Japanese Kanji Flashcard Generator

> Turn your kanji study sheets into Anki decks — no retyping needed.

KanGen takes **images of your study material** (tables, worksheets, textbook pages) and converts them into accurate, ready-to-import kanji flashcards. It uses OCR to read the image, a real Japanese dictionary to validate what it finds, and an optional AI layer to polish the output — but never to guess.

---

## Why KanGen?

You already have the study material. The annoying part is turning it into flashcards.

```
Before KanGen:  📸 study sheet  →  😩 manually type 40 kanji entries  →  📇 flashcards
After KanGen:   📸 study sheet  →  ⚡ run one command                  →  📇 flashcards
```

---

## Tech Stack

| Layer                | Technology                                                       |
|----------------------|------------------------------------------------------------------|
| **CLI**              | [Click](https://click.palletsprojects.com/)                      |
| **OCR**              | [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) (CPU/GPU)|
| **Image Processing** | OpenCV, Pillow, pillow-heif                                      |
| **Dictionary**       | [SudachiPy](https://github.com/WorksApplications/sudachi.rs)    |
| **LLM Enhancement**  | [Google Gemini](https://ai.google.dev/) (optional, batched)      |
| **Flashcard Output** | [genanki](https://github.com/kerrickstaley/genanki) → `.apkg`   |

---

## How the Pipeline Works

```
📸 Study Image
      ↓
🔲  Image Processing      — deskew, normalize, perspective correction
      ↓
🔤  OCR (PaddleOCR)       — extract text blocks + bounding boxes
      ↓
🔗  Spatial Grouping      — attach readings/meanings to the right kanji
      ↓
✅  Linguistic Validation  — verify against Sudachi dictionary
      ↓
✨  LLM Enhancement        — polish meanings + generate examples (optional)
      ↓
📦  Anki Deck (.apkg)     — import-ready flashcards
```

Each stage does **one job** and hands off clean data to the next.

---

## What Makes It Work

### 🎯 Kanji as Anchors
Instead of guessing at rows, columns, or table borders, KanGen treats each **kanji character as an anchor** and pulls in nearby text (readings, meanings, examples) based on spatial proximity. This makes it **layout-agnostic** — it doesn't care how your study sheet is formatted.

### 📚 Dictionary Truth, Not AI Guesses
Readings and meanings come from **SudachiPy**, a real Japanese morphological analyzer. The AI can polish your English meanings or pick the best example sentence, but it **cannot invent or override** what the dictionary says.

### 🔄 Fails Safely, Always
If OCR misreads something → confidence drops, card gets flagged.
If the LLM quota runs out → it finishes with dictionary-only data.
If one kanji fails → the rest still process.
No silent errors. No misleading cards.

---

## Supported Input

| ✅ Works great with         | ❌ Not supported (by design)  |
|-----------------------------|-------------------------------|
| Kanji tables                | Newspapers                    |
| Textbook pages              | Novels / manga                |
| Worksheets & study notes    | Handwritten kanji             |
| Photos with mild distortion | Unannotated running text      |

---

## Getting Started

### Requirements
- Python 3.10+
- Gemini API key *(optional — works without it, just with less polished output)*

### Setup & Run

```bash
# Clone and enter the project
git clone https://github.com/your-username/KanGen.git
cd KanGen

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Set your Gemini API key
echo "GEMINI_API_KEY=your_key_here" > .env

# Run on your study image
python src/main.py path/to/study_image.jpg
```

### CLI Options

```
Usage: main.py [OPTIONS] [INPUT_PATHS]...

Options:
  -o, --output TEXT    Output path for the Anki deck file (default: output_deck.apkg)
  --gpu / --no-gpu     Use GPU for OCR (requires CUDA, default: CPU)
  --api-key TEXT       Google Gemini API Key (or set GEMINI_API_KEY env var)
  --debug-images       Save debug images (blobs, contours)
  --no-warp            Skip perspective correction (process image as-is)
  --help               Show this message and exit
```

### Output
A single file: **`output_deck.apkg`** — drag it into Anki or AnkiDroid and you're done.

---

## Example Output

| Field    | Value                |
|----------|----------------------|
| Kanji    | 住                   |
| Meaning  | to live; to reside   |
| On-yomi  | ジュウ               |
| Kun-yomi | す(む)               |
| Example  | ここに住んでいます。  |

---

## Using Your Flashcards

KanGen outputs `.apkg` files — the standard Anki deck format.

| Platform               | App          | Cost          |
|------------------------|--------------|---------------|
| Windows / macOS / Linux| Anki Desktop | Free          |
| Android                | AnkiDroid    | Free          |
| iOS                    | AnkiMobile   | Paid (one-time)|
| Browser                | AnkiWeb      | Free          |

Download from [apps.ankiweb.net](https://apps.ankiweb.net), then **File → Import** your `.apkg`.

> **Tip:** Create a free [AnkiWeb](https://ankiweb.net) account to sync decks across devices.

---

## How LLM Usage Is Handled

Gemini's free tier is request-limited, not token-limited. KanGen **batches all kanji into a single API request** to stay within quota. If the API is unavailable or the key is missing, it falls back to dictionary-only mode automatically — no crash, no prompt.

---

## Project Status

### ✅ Shipped
- Full image → Anki deck pipeline
- Layout-agnostic kanji grouping
- On-yomi / Kun-yomi separation
- Dictionary validation via SudachiPy
- Batched Gemini LLM (quota-aware)
- Duplicate detection + empty card prevention
- Anki & AnkiDroid compatible `.apkg` output

### 🚧 Planned
- REST API
- Web interface (Streamlit prototype on `change/ui` branch)
- Persistent caching
- Confidence scores per card
- Multiple example sentences per kanji
- Additional export formats

---

## Known Limitations

- OCR accuracy depends on image quality — blurry or very dark photos will struggle
- Dense or unusual layouts may confuse the spatial grouping step
- Handwritten kanji is not supported
- Internal APIs are not stable yet — don't build on them

---

## Architecture

KanGen is built like something meant to become an API. Every stage is:

- **Stateless** — each request is independent
- **Modular** — swap out OCR, LLM, or dictionary without touching the rest
- **Validation-driven** — bad data gets caught before it becomes a flashcard
- **Batch-friendly** — designed for automation, not just one-off runs

---

## Contributing

Open to ideas, feedback, and contributions — especially in:

- **Japanese linguistics** — better validation, edge cases, reading rules
- **OCR robustness** — handling messier real-world photos
- **Study workflow design** — what do learners actually need?
- **API & frontend** — the next phase of the project

---

## License

To be determined before public release.

---

*KanGen works because it knows what it should not do.*
