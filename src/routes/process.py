from fastapi import APIRouter, UploadFile, BackgroundTasks
from models.schemas import JobResponse
from services.pipeline import run_pipeline
from services.storage import upload_file
import uuid
import shutil

router = APIRouter()

jobs = {}

@router.post("/process", response_model=JobResponse)
async def process_image(image:UploadFile, background_tasks:BackgroundTasks):
    job_id = str(uuid.uuid4())

    jobs[job_id] = {"status":"processing"}

    tmp_path = f"/tmp/{job_id}_{image.filename}"
    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(image.file, f)

    s3_key = f"inputs/{job_id}_{image.filename}"
    upload_file(tmp_path, s3_key)

    background_tasks.add_task(run_and_store, job_id, s3_key)

    return JobResponse(job_id=job_id)

async def run_and_store(job_id:str, file_path:str):
    result = run_pipeline(file_path=file_path, job_id=job_id)
    jobs[job_id] = result