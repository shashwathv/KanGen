from fastapi import FastAPI
from routes import jobs, process, download
from middleware.cors import add_cors

app = FastAPI(
    title="KanGen API",
    version="1.0.0",
    description="Turn kanji study sheet images into Anki flashcard decks"
)

add_cors(app=app)

app.include_router(jobs.router)
app.include_router(process.router)
app.include_router(download.router)

@app.get("/health")
def health():
    return {"status":"ok"}