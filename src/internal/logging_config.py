import logging
import sys
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
from pathlib import Path

current_job_id: ContextVar[str] = ContextVar("current_job_id", default="-")

_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)-22s | [job:%(job_id).8s] %(message)s"
_DATEFMT = "%H:%M:%S"
_FILE_DATEFMT = "%Y-%m-%d %H:%M:%S"


class JobIdFilter(logging.Filter):

    def filter(self, record: logging.LogRecord) -> bool:
        record.job_id = current_job_id.get()
        return True


def setup_logging(level: int = logging.INFO, log_dir: str = "logs") -> None:
    root = logging.getLogger()
    if getattr(root, "_kangen_configured", False):
        return

    job_filter = JobIdFilter()

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.addFilter(job_filter)
    console.setFormatter(logging.Formatter(fmt=_FORMAT, datefmt=_DATEFMT))

    # Rotating file handler
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_path / "kangen.log",
        maxBytes=5 * 1024 * 1024,   # 5 MB per file
        backupCount=5,              # keep 5 old files
        encoding="utf-8",
    )
    file_handler.addFilter(job_filter)
    file_handler.setFormatter(logging.Formatter(fmt=_FORMAT, datefmt=_FILE_DATEFMT))

    root.handlers.clear()
    root.addHandler(console)
    root.addHandler(file_handler)
    root.setLevel(level)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    root._kangen_configured = True


def set_job_id(job_id: str):
    current_job_id.set(job_id)