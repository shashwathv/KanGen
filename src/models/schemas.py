from pydantic import BaseModel
from typing import Optional
from enum import Enum

class JobResponse(BaseModel):
    job_id: str

class Status(str, Enum):
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"

class ProcessingStats(BaseModel):
    created: int
    skipped: int
    total_processed: int

class JobStatus(BaseModel):
    status: Status
    error: Optional[str] = None
    stats: Optional[ProcessingStats] = None
    download_url: Optional[str] = None

class HealthResponse(BaseModel):
    status: str