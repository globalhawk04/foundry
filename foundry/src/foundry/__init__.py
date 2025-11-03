# FILE: src/foundry/__init__.py

# --- Expose the core models ---
from .models import (
    Base,
    User,
    Job,
    FoundryClarificationRequest,
    CorrectionRecord
)

# --- Expose the main handler from the correction module ---
from .correction import CorrectionHandler, render_correction_form

# --- Expose the core pipeline abstractions ---
from .pipeline import Pipeline, Phase, PhaseExecutionError

# --- Expose the Celery integration components ---
from .celery_integration import celery_app, register_pipeline, run_foundry_pipeline

# --- Expose the status polling functions ---
from .status import update_status, get_status, clear_status

# --- Expose the human-in-the-loop components ---
from .human_in_the_loop import AmbiguityDetector, HumanInTheLoopPhase, render_clarification_feed

__all__ = [
    # Models
    "Base",
    "User",
    "Job",
    "FoundryClarificationRequest",
    "CorrectionRecord",
    # Correction Module
    "CorrectionHandler",
    "render_correction_form",
    # Pipeline Module
    "Pipeline",
    "Phase",
    "PhaseExecutionError",
    # Celery Integration
    "celery_app",
    "register_pipeline",
    "run_foundry_pipeline",
    # Status Module
    "update_status",
    "get_status",
    "clear_status",
    # Human-in-the-Loop Module
    "AmbiguityDetector",
    "HumanInTheLoopPhase",
    "render_clarification_feed",
]
