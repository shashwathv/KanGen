from fastapi import APIRouter, HTTPException
from models.schemas import JobStatus
from services.jobs_store import job_store

router = APIRouter()

@router.get("/jobs/{job_id}", response_model=JobStatus)
def get_job_status(job_id: str):
    job = job_store.get(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatus(**job)   