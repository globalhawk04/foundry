# FILE: app/gpu_lock.py

import os
import time

# Use a path inside the container's data directory for the lock file
LOCK_FILE = "data/gpu.lock"

class GPULock:
    """
    A simple file-based lock to ensure exclusive access to the GPU.

    This is used as a context manager:
    with GPULock():
        # Code that uses the GPU runs here
    """
    def __init__(self, owner: str = "Unknown"):
        self.owner = owner

    def __enter__(self):
        print(f"[{self.owner}] Attempting to acquire GPU lock...")
        while os.path.exists(LOCK_FILE):
            time.sleep(2) # Wait if the lock is held by another process
        
        # Acquire the lock by creating the file
        with open(LOCK_FILE, 'w') as f:
            f.write(self.owner)
        
        print(f"[{self.owner}] GPU lock acquired.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
        print(f"[{self.owner}] GPU lock released.")