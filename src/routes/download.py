from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from routes.process import jobs

router = APIRouter()

@router.get("/download/{job_id}")
def download(job_id:str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.get("status") != "done":
        raise HTTPException(status_code=400, detail="File not ready")
    
    output_path = job.get("output_path")
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="File path does not exist")
    
    return FileResponse(
        path=output_path, 
        media_type="application/octet-stream", 
        filename="kanji_deck.apkg"
    )