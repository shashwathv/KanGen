from pydantic import BaseModel
from typing import List, Optional
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

class CardOut(BaseModel):
    kanji: str
    meaning: str
    on_yomi: str = ""
    kun_yomi: str = ""
    example: str = ""

class JobStatus(BaseModel):
    status: Status
    error: Optional[str] = None
    cards: Optional[List[CardOut]] = None     
    download_url: Optional[str] = None
    stats: Optional[ProcessingStats] = None

class BuildRequest(BaseModel):
    cards: List[CardOut]
    job_id: Optional[str] = None 

class BuildResponse(BaseModel):
    download_url: str
    stats: ProcessingStats