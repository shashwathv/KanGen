from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from services.jobs_store import job_store
from services.storage import get_presigned_url

router = APIRouter()

@router.get("/download/{job_id}")
def download(job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.get("status") != "done":
        raise HTTPException(status_code=400, detail="File not ready")
        
    s3_key = job.get("s3_key")
    if s3_key:
        url = get_presigned_url(s3_key)
        if url:
            return RedirectResponse(url=url)


    download_url = job.get("download_url")
    if download_url:
        return RedirectResponse(url=download_url)

    raise HTTPException(status_code=404, detail="Download URL not available")