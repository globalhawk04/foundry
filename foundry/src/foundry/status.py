# FILE: foundry/status.py

import redis
import json
import os

# --- 1. Redis Client Setup ---
# In a real application, this might be a shared client.
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=2, decode_responses=True)

STATUS_KEY_PREFIX = "foundry_job_status"
KEY_EXPIRATION_SECONDS = 3600  # 1 hour

# --- 2. Core Status Functions ---

def update_status(job_id: int, status: str, message: str, progress: int):
    """
    Updates the status of a job in Redis.

    This function is designed to be called from within a background task or pipeline phase.
    It stores a structured JSON object for rich status updates.

    Args:
        job_id: The ID of the job being updated.
        status: The current state (e.g., 'in_progress', 'completed', 'failed').
        message: A user-friendly message to display in the UI.
        progress: A progress percentage (0-100).
    """
    key = f"{STATUS_KEY_PREFIX}:{job_id}"
    payload = {
        "status": status,
        "message": message,
        "progress": min(max(progress, 0), 100), # Clamp value between 0 and 100
    }
    try:
        redis_client.set(key, json.dumps(payload), ex=KEY_EXPIRATION_SECONDS)
    except redis.exceptions.RedisError as e:
        print(f"--- [Status Error] Could not update status for Job {job_id}: {e} ---")

def get_status(job_id: int) -> dict | None:
    """
    Retrieves the status of a job from Redis.

    This is designed to be called from a web server endpoint that the frontend polls.

    Args:
        job_id: The ID of the job to check.

    Returns:
        A dictionary with the status information, or None if not found.
    """
    key = f"{STATUS_KEY_PREFIX}:{job_id}"
    try:
        status_json = redis_client.get(key)
        if status_json:
            return json.loads(status_json)
    except redis.exceptions.RedisError as e:
        print(f"--- [Status Error] Could not retrieve status for Job {job_id}: {e} ---")
    return None

def clear_status(job_id: int):
    """Removes a job's status key from Redis, typically after a job is complete."""
    key = f"{STATUS_KEY_PREFIX}:{job_id}"
    try:
        redis_client.delete(key)
    except redis.exceptions.RedisError as e:
        print(f"--- [Status Error] Could not clear status for Job {job_id}: {e} ---")
