# FILE: main_app.py

from sqlalchemy.orm import Session
from foundry.models import Job
from foundry.celery_integration import register_pipeline, run_foundry_pipeline
from my_pipelines import UppercasePipeline

# --- Application Startup ---
# This is the crucial step: register your pipeline with a unique name.
register_pipeline(name="uppercase_pipeline", pipeline_class=UppercasePipeline)


# --- Example: A function to start a new job ---
# In a web app, this would be your API endpoint.
def start_new_job(db: Session, text_to_process: str):
    # 1. Create a Job record in the database.
    new_job = Job(
        owner_id=1, # In a real app, this would be the current user's ID
        status="pending",
        input_data={"content": text_to_process}
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    print(f"--- Job {new_job.id} created. Dispatching to Celery... ---")

    # 2. Dispatch the background task.
    # We tell Celery to run our generic task, passing it the name
    # of the pipeline we want to use and the ID of the job to process.
    run_foundry_pipeline.delay(
        pipeline_name="uppercase_pipeline", 
        job_id=new_job.id
    )
    
    return new_job.id
