from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from routes.process import jobs

router = APIRouter()

@router.get("/download/{job_id}")
def download(job_id:str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.get("status") != "done":
        raise HTTPException(status_code=400, detail="File not ready")
    
    download_url = job.get("download_url")
    if not download_url:
        raise HTTPException(status_code=404, detail="Download URL not available")
    
    return RedirectResponse(url=download_url)