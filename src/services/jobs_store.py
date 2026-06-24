import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

JOB_TTL = 60 * 60  
_KEY_PREFIX = "kangen:job:"


class JobStore:
    def __init__(self, redis_url: Optional[str] = None):
        self._mem = {}    
        self._redis = None
        url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            import redis

            client = redis.Redis.from_url(url, decode_responses=True)
            client.ping()    
            self._redis = client
            logger.info("JobStore connected to Redis at %s", url)
        except Exception as e:
            logger.warning(
                "Redis unavailable (%s); falling back to in-memory store. "
                "Jobs will NOT survive restarts and multi-worker will break.", e
            )

    def set(self, job_id: str, data: dict) -> None:
        if self._redis is not None:
            self._redis.set(_KEY_PREFIX + job_id, json.dumps(data), ex=JOB_TTL)
        else:
            self._mem[job_id] = data

    def get(self, job_id: str) -> Optional[dict]:
        if self._redis is not None:
            raw = self._redis.get(_KEY_PREFIX + job_id)
            return json.loads(raw) if raw else None
        return self._mem.get(job_id)


job_store = JobStore()