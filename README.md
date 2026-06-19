# 漢 KanGen

### Japanese Kanji Flashcard Generator

> Turn your Japanese study sheets into Anki decks — no retyping required.

KanGen converts images of kanji study material into structured, import-ready Anki flashcards. Upload a worksheet, textbook page, or handwritten study table, and KanGen extracts the kanji, validates the readings, and generates a `.apkg` deck automatically.

Built with multimodal AI, dictionary-backed validation, and a production-ready API, KanGen eliminates the tedious process of manually creating flashcards from study resources.

---

## ✨ Features

- 📸 Extract kanji directly from study sheets and textbook pages
- 👁️ Multimodal page understanding using Gemini 2.5 Flash
- 🛡️ Reading validation with SudachiPy to reduce hallucinations
- 📇 Automatic Anki deck generation (`.apkg`)
- ⚡ Command-line interface for local use
- 🌐 FastAPI backend for web integrations
- ☁️ AWS S3 integration with presigned download URLs
- 🔄 Built-in retry and backoff handling for API rate limits
- 🧹 Automatic cleanup of temporary files

---

## Why KanGen?

You already have the study material.

The difficult part is turning it into flashcards.

```text
Before KanGen

📸 Study Sheet
      ↓
😩 Manually type dozens of entries
      ↓
📇 Flashcards

After KanGen

📸 Study Sheet
      ↓
⚡ One Command
      ↓
📇 Flashcards
```

Instead of spending time copying kanji, readings, and meanings into Anki, KanGen performs the entire workflow automatically.

---

## 🏗 Architecture

```text
📸 Study Image
      ↓
🔲 Image Preprocessing
      ↓
👁️ Gemini 2.5 Flash
      ↓
📋 Structured JSON Extraction
      ↓
🛡️ SudachiPy Validation
      ↓
📇 genanki Deck Generation
      ↓
📦 .apkg Output
      ↓
☁️ S3 Upload (API Mode)
```

---

## 🧠 How It Works

### 1. Image Preprocessing

Input images are normalized before extraction.

Supported formats include:

- JPG
- PNG
- HEIC

Images are converted when necessary and prepared for visual analysis.

---

### 2. Vision Extraction

KanGen uses Gemini 2.5 Flash to understand the structure of Japanese study material.

Unlike traditional OCR systems, the model can distinguish between:

- Actual study content
- Stroke-order diagrams
- Practice boxes
- Decorative annotations
- Layout elements

The output is structured JSON rather than raw text.

---

### 3. Dictionary Validation

Multimodal models are powerful but not infallible.

To reduce incorrect readings, KanGen validates extracted readings against SudachiPy.

This creates a hybrid workflow:

```text
AI Extraction
      +
Dictionary Validation
      =
Reliable Flashcards
```

---

### 4. Deck Generation

Validated entries are converted into Anki flashcards using `genanki`.

Generated decks are compatible with:

- Anki Desktop
- AnkiDroid
- AnkiMobile
- AnkiWeb

---

## 🛠 Tech Stack

| Layer | Technology |
|---------|------------|
| Vision Engine | Gemini 2.5 Flash |
| Validation | SudachiPy |
| CLI | Click |
| REST API | FastAPI + Uvicorn |
| Cloud Storage | AWS S3 (Boto3) |
| Flashcard Generation | genanki |
| Data Models | Pydantic |

---

## 📦 Installation

### Requirements

- Python 3.10+
- Google Gemini API Key

### Clone Repository

```bash
git clone https://github.com/your-username/KanGen.git
cd KanGen
```

### Create Virtual Environment

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file:

```env
GEMINI_API_KEY=your_api_key

# Required only for API mode
S3_BUCKET=your_bucket_name
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

---

## 🚀 Usage

### CLI Mode

Generate a deck directly from one or more images.

```bash
python src/main.py study_sheet.jpg
```

Specify an output path:

```bash
python src/main.py study_sheet.jpg \
    --output my_kanji_deck.apkg
```

### CLI Options

```text
Usage: main.py [OPTIONS] [INPUT_PATHS]...

Options:
  -o, --output TEXT
      Output deck path

  --api-key TEXT
      Gemini API key

  --help
      Show help message
```

---

## 🌐 API Mode

Start the FastAPI server:

```bash
uvicorn src.api:app --reload
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

### Endpoints

#### Create Processing Job

```http
POST /v1/process
```

Upload an image and receive a job identifier.

Response:

```json
{
  "job_id": "abc123"
}
```

#### Check Job Status

```http
GET /v1/jobs/{job_id}
```

Response:

```json
{
  "status": "completed",
  "download_url": "..."
}
```

A presigned S3 URL is returned when deck generation completes.

---

## 📖 Example Flashcard

| Field | Value |
|---------|---------|
| Kanji | 住 |
| Meaning | To live; reside |
| On-yomi | ジュウ |
| Kun-yomi | す(む) |
| Example Sentence | ここに住んでいます。 |

---

## 📚 Supported Input

### Recommended

- Kanji study tables
- Textbook pages
- Worksheets
- Vocabulary sheets
- Annotated study notes

### Not Supported

- Newspapers
- Novels
- Manga
- Long-form running text
- General document OCR

KanGen is optimized specifically for educational study material.

---

## ⚙️ Reliability Features

### Automatic Retries

Handles temporary failures such as:

- HTTP 429 (Rate Limits)
- HTTP 503 (Service Unavailable)

with exponential backoff.

### Background Processing

Long-running generation tasks execute in worker threads, keeping the API responsive.

### Resource Cleanup

Temporary images and generated decks are automatically removed after processing.

---

## 📲 Importing Decks

KanGen generates standard `.apkg` files.

| Platform | Application |
|-----------|------------|
| Windows | Anki Desktop |
| macOS | Anki Desktop |
| Linux | Anki Desktop |
| Android | AnkiDroid |
| iOS | AnkiMobile |
| Browser | AnkiWeb |

Import through:

```text
File → Import → Select .apkg
```

---

## 🗺 Roadmap

### Completed

- Gemini 2.5 Flash extraction
- Structured JSON output
- On-yomi / Kun-yomi separation
- SudachiPy validation
- genanki integration
- FastAPI backend
- AWS S3 delivery
- Retry handling
- Automatic cleanup

### Planned

- Next.js web interface
- Redis job queue
- Persistent image caching
- Multiple example sentences
- Batch deck generation
- User authentication
- Deck customization options

---

## 🏛 Design Principles

### Stateless

Each request is independent and self-contained.

### Schema-Driven

All outputs are validated through typed models before deck generation.

### Fail-Safe

Temporary resources are cleaned aggressively and external API failures are handled gracefully.

---

## 📄 License


---

> KanGen works because it understands not only what to extract, but also what to ignore.