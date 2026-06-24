import uuid 
import os 
from pathlib import Path 
from fastapi import APIRouter, HTTPException
from models.schemas import BuildRequest, BuildResponse, ProcessingStats
from internal.anki import AnkiGenerator
from services.storage import upload_file, get_presigned_url
from services.jobs_store import job_store
from internal.logging_config import set_job_id

router = APIRouter()

@router.post("/build", response_model=BuildResponse)
def build_deck(payload: BuildRequest):
    if not payload.cards:
        raise HTTPException(400, "No cards provided.")

    job_id = payload.job_id or str(uuid.uuid4())
    set_job_id(job_id)
    anki = AnkiGenerator()
    for c in payload.cards:
        anki.add_card(c.kanji, c.meaning, c.on_yomi, c.kun_yomi, c.example)

    output_path = Path(f"/tmp/{job_id}_output.apkg")
    try:
        if not anki.save_package(output_path):
            raise HTTPException(400, "No valid cards to build into a deck.")

        s3_key = f"outputs/{job_id}_output.apkg"
        if not upload_file(str(output_path), s3_key):
            raise HTTPException(502, "Failed to store the deck")

        url = get_presigned_url(s3_key)
        stats = anki.get_statistics()
        job = job_store.get(job_id) or {}
        job.update({
            "status": "done",
            "s3_key": s3_key,
            "download_url": url,
            "stats": stats,
        })
        job_store.set(job_id, job)

        return BuildResponse(
            download_url=url,
            stats=ProcessingStats(**stats),
        )
    finally:
        if output_path.exists():
            try:
                os.remove(output_path)
            except Exception:
                pass