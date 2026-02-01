# 漢 KanGen
### Japanese Kanji Flashcard Generator

> Turn your kanji study sheets into Anki decks — no retyping needed.

KanGen takes **images of your study material** (tables, worksheets, textbook pages) and converts them into accurate, ready-to-import kanji flashcards. It uses OCR to read the image, a real Japanese dictionary to validate what it finds, and an optional AI layer to polish the output — but never to guess.

---

## Why KanGen?

You already have the study material. You already know *what* you need to learn. The annoying part is turning it into flashcards.

KanGen automates exactly that step — and nothing more. It's intentionally narrow, and that's what makes it reliable.

```
Before KanGen:  📸 study sheet  →  😩 manually type 40 kanji entries  →  📇 flashcards
After KanGen:   📸 study sheet  →  ⚡ run one command                  →  📇 flashcards
```

---

## What makes it work

### 🎯 Kanji as anchors
Instead of guessing at rows, columns, or table borders, KanGen treats each **kanji character as an anchor** and pulls in nearby text (readings, meanings, examples) based on spatial proximity. This is what makes it **layout-agnostic** — it doesn't care how your study sheet is formatted.

### 📚 Dictionary truth, not AI guesses
Readings and meanings come from **SudachiPy**, a real Japanese morphological analyzer. The AI can polish your English meanings or pick the best example sentence, but it **cannot invent or override** what the dictionary says. This is the single most important reason KanGen doesn't hallucinate.

### 🔄 Fails safely, always
If OCR misreads something → confidence drops, card gets flagged.  
If the LLM quota runs out → it finishes with dictionary-only data.  
If one kanji fails → the rest still process.  
No silent errors. No misleading cards.

---

## How the pipeline works

```
📸 Study Image
      ↓
🔲  Image Processing      — deskew, normalize, perspective correction
      ↓
🔤  OCR                   — extract text blocks + bounding boxes
      ↓
🔗  Spatial Grouping      — attach readings/meanings to the right kanji
      ↓
✅  Linguistic Validation  — verify against Sudachi dictionary
      ↓
✨  LLM Enhancement        — polish meanings + generate examples (optional)
      ↓
📦  Anki Deck (.apkg)     — import-ready flashcards
```

Each stage does **one job** and hands off clean data to the next. This makes the whole system debuggable, replaceable, and ready to grow into an API later.

---

## ✅ What's supported

| ✅ Works great with         | ❌ Not supported (by design)  |
|-----------------------------|-------------------------------|
| Kanji tables                | Newspapers                    |
| Textbook pages              | Novels / manga                |
| Worksheets & study notes    | Handwritten kanji             |
| Photos with mild distortion | Unannotated running text      |

KanGen doesn't support newspapers or novels because those require reading disambiguation, frequency modeling, and context-based inference — entirely different problems. Refusing to guess is how it stays accurate.

---

## 📦 What's built vs. what's coming

### ✅ Shipped
- Full image → Anki deck pipeline
- Layout-agnostic kanji grouping
- On-yomi / Kun-yomi separation
- Dictionary validation via Sudachi
- Batched Gemini LLM (quota-aware)
- Duplicate detection + empty card prevention
- Anki & AnkiDroid compatible `.apkg` output

### 🚧 Planned
- REST API
- Web interface
- Persistent caching
- Confidence scores per card
- Multiple example sentences per kanji
- Additional export formats

---

## 🚀 Getting Started

### Requirements
- Python 3.10+
- Gemini API key *(optional — the tool works without it, just with less polished output)*

### Setup & Run

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run on your study image
python main.py path/to/study_image.jpg
```

### Output
A single file: **`output_deck.apkg`** — drag it into Anki or AnkiDroid and you're done.

---

## 📲 Setting Up Anki

KanGen outputs `.apkg` files — the standard Anki deck format. To use them, you need Anki installed on at least one device. Here's how to get it set up.

> **What is Anki?**  
> Anki is a spaced repetition flashcard app. It shows you cards just before you're about to forget them, so you study less and remember more. It's the industry standard for language learning — and it's free on desktop.

### Download Anki

| Platform | App | Cost | Official Link |
|----------|-----|------|---------------|
| Windows / macOS / Linux | Anki Desktop | **Free** | [https://apps.ankiweb.net](https://apps.ankiweb.net) |
| Android | AnkiDroid | **Free** | [Google Play Store](https://play.google.com/store/apps/details?id=com.ichi2.anki) |
| iOS (iPhone / iPad) | AnkiMobile | Paid (one-time) | [App Store](https://apps.apple.com/us/app/ankimobile-flashcards/id373493387) |
| Browser (any device) | AnkiWeb | **Free** | [https://ankiweb.net](https://ankiweb.net) |

> ⚠️ **Watch out for fakes.** There are many apps with "Anki" in the name that are *not* made by the Anki team. Only the apps linked above are part of the official Anki ecosystem and are compatible with `.apkg` files.

### Import Your KanGen Deck

#### On Desktop (Windows / macOS / Linux) — Recommended first step

```
1. Run KanGen → generates output_deck.apkg
2. Open Anki Desktop
3. Click "Import file" on the main screen (or press Ctrl+O)
4. Select your output_deck.apkg file
5. Click "Import" — done ✅
```

#### On Android (AnkiDroid)

```
Option A — Direct import:
1. Copy output_deck.apkg to your phone (USB, cloud, or email it to yourself)
2. Open the .apkg file on your phone → AnkiDroid opens it automatically
3. Tap "Import" → done ✅

Option B — Sync from desktop:
1. Import the deck into Anki Desktop first (see above)
2. Click "Sync" in Anki Desktop (needs a free AnkiWeb account)
3. Open AnkiDroid → tap "Sync" → your deck appears ✅
```

#### On iOS (AnkiMobile)

```
Option A — Direct import:
1. Email or AirDrop the .apkg file to your iPhone
2. Open the file → AnkiMobile launches automatically
3. Tap "Import" → done ✅

Option B — Sync from desktop:
1. Import the deck into Anki Desktop first
2. Sync on desktop (needs a free AnkiWeb account)
3. Open AnkiMobile → tap the sync button → your deck appears ✅
```

### Quick Tips
- **Free AnkiWeb account** — Sign up at [ankiweb.net](https://ankiweb.net). It lets you sync decks across all your devices for free. Highly recommended if you study on both desktop and mobile.
- **Re-running KanGen** — If you regenerate a deck from the same image, importing again won't duplicate cards. Anki detects and skips duplicates automatically.
- **Deck not showing up?** — Make sure you imported the `.apkg` file, not a `.zip` or other format. KanGen only outputs `.apkg`.

---

## 📖 Example Output

| Field    | Value                |
|----------|----------------------|
| Kanji    | 住                   |
| Meaning  | to live; to reside   |
| On-yomi  | ジュウ               |
| Kun-yomi | す(む)               |
| Example  | ここに住んでいます。  |

---

## 🔑 How LLM usage is handled

Gemini's free tier is request-limited, not token-limited. So KanGen **batches multiple kanji into a single request** to stay well within quota. If the API is unavailable or the key is missing, it falls back to dictionary-only mode automatically — no crash, no prompt.

---

## ⚠️ Known Limitations

Being honest about what doesn't work yet:

- OCR accuracy depends on image quality — blurry or very dark photos will struggle.
- Dense or unusual layouts may confuse the spatial grouping step.
- Handwritten kanji is not supported.
- Internal APIs are not stable yet — don't build on them.

These are known, tracked, and being worked on.

---

## 🏗️ Why the architecture is solid

KanGen is built like something that's meant to become an API — even though it's currently a CLI tool. Every stage is:

- **Stateless** — each request is independent
- **Modular** — swap out OCR, LLM, or dictionary without touching the rest
- **Validation-driven** — bad data gets caught before it becomes a flashcard
- **Batch-friendly** — designed for automation, not just one-off runs

When the REST API and web UI come, the core pipeline stays exactly the same.

---

## 🤝 Contributing

The project is open to ideas, feedback, and contributions — especially in these areas:

- **Japanese linguistics** — better validation, edge cases, reading rules
- **OCR robustness** — handling messier real-world photos
- **Study workflow design** — what do learners actually need?
- **API & frontend** — the next phase of the project

---

## 📄 License

To be determined before public API release.

---

*KanGen works because it knows what it should not do.*
