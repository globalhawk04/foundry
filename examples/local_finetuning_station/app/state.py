# FILE: app/state.py

from enum import Enum
import os
import json

# --- ADD THIS NEW ENUM ---
class AppMode(Enum):
    """Defines the user-selected AI task."""
    OCR = "OCR"
    OBJECT_DETECTION = "Object Detection"



class AppStatus(Enum):
    """
    Defines the possible states of the application.
    This acts as a simple state machine.
    """
    IDLE = "IDLE"                         # Server is running, waiting for upload
    INFERENCE = "INFERENCE"               # Inference is running in a background worker
    CORRECTION = "CORRECTION"  
    PRE_TRAINING = "PRE_TRAINING"            # User is actively correcting in the UI
    TRAINING = "TRAINING"                 # Training is running in a background worker
    COMPLETE = "COMPLETE"                 # Training is finished, results are available
    ERROR = "ERROR"                       # An error occurred in a background worker

class AppState:
    """
    A simple class to manage the global state of the application.
    This is not thread-safe for writing from multiple web requests at once,
    but it's sufficient for our single-user, modal application.
    """
    STATUS = AppStatus.IDLE
    STATUS_MESSAGE = "Ready to accept image uploads."
    MODEL_TYPE: AppMode = AppMode.OCR # Default value
    
    @classmethod
    def set_status(cls, status: AppStatus, message: str):
        """Updates the application's global state."""
        print(f"--- State Change: {cls.STATUS.value} -> {status.value} ({message}) ---")
        cls.STATUS = status
        cls.STATUS_MESSAGE = message

    @classmethod
    def get_status(cls) -> dict:
        """Returns the current state as a dictionary."""
        return {"status": cls.STATUS.value, "message": cls.STATUS_MESSAGE}