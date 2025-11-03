# FILE: foundry/celery_integration.py

import os
from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Assume a shared settings/config file might exist in a full app
# For now, we'll configure it directly.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///foundry_quickstart.db")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

# --- 1. Celery Application Setup ---
celery_app = Celery("foundry_tasks", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

# --- 2. Database Setup for Celery Workers ---
# Celery workers are separate processes and need their own synchronous DB connections.
engine = create_engine(DATABASE_URL)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- 3. Pipeline Registry ---
# This dictionary makes user-defined pipelines discoverable by the Celery task.
# The main application will register its pipelines here at startup.
PIPELINE_REGISTRY = {}

def register_pipeline(name: str, pipeline_class):
    """
    Registers a Pipeline class so it can be found by the Celery worker.

    Args:
        name: A unique string identifier for the pipeline.
        pipeline_class: The Pipeline class (not an instance) to register.
    """
    from .pipeline import Pipeline  # Local import to avoid circular dependency
    if not issubclass(pipeline_class, Pipeline):
        raise TypeError(f"{pipeline_class.__name__} must be a subclass of Pipeline.")
    
    print(f"--- Registering pipeline: '{name}' ---")
    PIPELINE_REGISTRY[name] = pipeline_class

# --- 4. Generic Celery Task ---
@celery_app.task(name="run_foundry_pipeline")
def run_foundry_pipeline(pipeline_name: str, job_id: int):
    """
    A generic Celery task that finds and executes a registered Foundry Pipeline.
    """
    db = SyncSessionLocal()
    try:
        print(f"--- [Celery Worker] Received job {job_id} for pipeline '{pipeline_name}' ---")
        
        # 1. Look up the pipeline class from the registry
        pipeline_class = PIPELINE_REGISTRY.get(pipeline_name)
        
        if not pipeline_class:
            # If the pipeline isn't registered, fail the job gracefully.
            from .models import Job
            job = db.get(Job, job_id)
            if job:
                job.status = "failed"
                job.error_message = f"Pipeline '{pipeline_name}' is not registered."
                db.commit()
            raise ValueError(f"Pipeline '{pipeline_name}' is not registered.")
            
        # 2. Instantiate the pipeline with a fresh DB session
        pipeline = pipeline_class(db_session=db)
        
        # 3. Execute the pipeline
        pipeline.run(job_id=job_id)
        
        print(f"--- [Celery Worker] Finished processing job {job_id} ---")

    except Exception as e:
        print(f"--- [Celery Worker] An error occurred in job {job_id}: {e} ---")
        # You might want to add more robust error handling/retry logic here.
    finally:
        # CRITICAL: Always close the database session in a worker.
        db.close()
