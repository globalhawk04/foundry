How to Use This README.md

This content should be saved as README.md in a new directory, for example, examples/full_asynchronous_pipeline/.

The main_app.py and my_pipelines.py files should be placed in that same directory.

Users will also need to create one more small file, run_main.py, which is provided in the instructions below.

Foundry Example: Production-Grade Asynchronous Pipelines

This example demonstrates the complete, production-ready architecture for using Foundry. It moves beyond the self-contained quickstarts to show how a main application can asynchronously delegate work to a separate pool of background workers using Celery and Redis.

This is the blueprint for building scalable, resilient, and non-blocking AI systems with Foundry.

Goal

To show how a web server or application can receive a request, create a Job, and immediately offload the intensive data processing to a background Celery worker without blocking the main application.

Core Concepts Demonstrated

Custom Pipeline Definition: Defining a multi-step Pipeline with custom Phases in my_pipelines.py.

Asynchronous Task Dispatching: Using Celery to run a Foundry pipeline in a separate process.

The Pipeline Registry: The critical pattern of using register_pipeline to make your custom pipelines discoverable by the background workers.

Decoupled Architecture: The main application (main_app.py) only needs to know the name of a pipeline, not how it's implemented.

File Breakdown

my_pipelines.py: The "Worker Logic." This file defines the actual steps of the data processing pipeline. It knows how to do the work. It has no knowledge of Celery or web servers.

main_app.py: The "Job Dispatcher." This represents your main application (e.g., a FastAPI or Flask web server). It knows when to start a job. Its primary roles are to create a Job in the database and send a message to the Celery queue.

How to Run This Example

This example requires external services (Redis and Celery) to be running.

Prerequisites

Install Celery and Redis: Ensure you are in your project's virtual environment.



Install and Run Redis: You need a running Redis server. If you have it installed locally, you can typically start it by running:

Leave this running in its own terminal.

Step 1: Start the Celery Worker

The Celery worker is the background process that will listen for new jobs and execute our pipeline.

Open a new terminal, navigate to the project's root foundry/ directory, and run the following command. (This assumes your foundry package is installed in editable mode or is in your PYTHONPATH).


# Run this from the project's root directory
celery -A foundry.celery_integration.celery_app worker --loglevel=info

You should see the Celery worker start up and print a "ready" message. Leave this terminal running. It is now waiting for tasks.

Step 2: Create a Script to Run the Main App

In the same directory as main_app.py and my_pipelines.py, create a new file named run_main.py. This script will set up a database session and call our start_new_job function, simulating a request to our application.


# FILE: run_main.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from foundry.models import Base
from main_app import start_new_job # Import our job-starting function

# --- Database Setup ---
DB_FILE = "foundry_celery_example.db"
engine = create_engine(f"sqlite:///{DB_FILE}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the database tables if they don't exist
Base.metadata.create_all(bind=engine)

# --- Main Execution ---
if __name__ == "__main__":
    print("--- Simulating a request to the main application... ---")
    db = SessionLocal()
    
    # The text we want our background pipeline to process
    text_to_process = "hello from the asynchronous world!"
    
    # This will create the DB job and dispatch the Celery task
    job_id = start_new_job(db, text_to_process)
    
    print(f"--- Main application finished its request. Job {job_id} is now processing in the background. ---")
    
    db.close()
Step 3: Run the Main App and Observe

Now, open a third terminal, navigate to this example's directory, and run the script:


In your run_main.py terminal, you will see:


--- Simulating a request to the main application... ---
--- Job 1 created. Dispatching to Celery... ---
--- Main application finished its request. Job 1 is now processing in the background. ---

Notice how it finishes almost instantly. It did not wait for the text to be converted to uppercase.

Now, look at your Celery Worker terminal. You will see the log output from the pipeline executing in the background:


[2025-11-03 19:50:00,000: INFO/MainProcess] Task run_foundry_pipeline[<task_id>] received
--- [Celery Worker] Received job 1 for pipeline 'uppercase_pipeline' ---
--- [Job 1] Running Phase: ExtractTextPhase ---
--- [Job 1] Phase 'ExtractTextPhase' Succeeded. State saved. ---
--- [Job 1] Running Phase: ConvertToUppercasePhase ---
--- [Job 1] Phase 'ConvertToUppercasePhase' Succeeded. State saved. ---
--- [Job 1] Pipeline finished successfully. ---
--- [Celery Worker] Finished processing job 1 ---
[2025-11-03 19:50:01,000: INFO/MainProcess] Task run_foundry_pipeline[<task_id>] succeeded

You have successfully run a full, decoupled, asynchronous data processing job using Foundry! The final result (HELLO FROM THE ASYNCHRONOUS WORLD!) is now saved in the foundry_celery_example.db SQLite file.
