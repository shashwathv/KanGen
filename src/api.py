from fastapi import APIRouter, FastAPI
from routes import jobs, process, download
from middleware.cors import add_cors

app = FastAPI(
    title="KanGen API",
    version="1.0.0",
    description="Turn kanji study sheet images into Anki flashcard decks"
)

add_cors(app=app)

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(jobs.router)
v1_router.include_router(process.router)
v1_router.include_router(download.router)

app.include_router(v1_router)

@app.get("/health")
def health():
    return {"status":"ok"}