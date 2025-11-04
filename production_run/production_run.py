# FILE: examples/production_run/production_run.py

import os
import uvicorn
import questionary
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# --- Use Case Imports ---
# These provide the domain-specific logic and data for the simulation
from use_cases.mock_data import mock_invoice_results, mock_pole_detection_results
from use_cases.simulators import MockAISimulator

# --- Foundry & Application Imports ---
# These are the core framework components and our specific implementation of them
from foundry.models import Base, User, Job
from app.pipeline import build_pipeline

# This import will create the FastAPI 'app' object
from app.main import app, AppState


def setup_database():
    """
    Sets up a clean, in-memory SQLite database for a single run.
    """
    print("--- Setting up in-memory SQLite database... ---")
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def create_initial_jobs(db_session, use_case: str):
    """
    Creates a batch of Foundry Job objects in the database for the chosen use case.
    """
    print(f"--- Creating initial jobs for use case: {use_case} ---")
    
    # All jobs will be owned by a single dummy user for this example
    user = User(username="default_user")
    db_session.add(user)
    db_session.commit()

    # Determine which directory of static images to use
    if use_case == "Invoice Processing":
        image_dir = os.path.join("static", "invoices")
    else: # Utility Pole Detection
        image_dir = os.path.join("static", "poles")

    # Find all image files in the directory
    image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    job_ids = []
    for image_file in image_files:
        job = Job(
            owner_id=user.id,
            status="pending",
            input_data={
                "type": "image",
                "url": f"/{image_dir}/{image_file}" # The URL the browser will use
            }
        )
        db_session.add(job)
        db_session.commit()
        job_ids.append(job.id)
    
    print(f"--- Created {len(job_ids)} jobs. ---")
    return job_ids


def run_initial_ai_simulation(db_session, job_ids: list, simulator: MockAISimulator, threshold: float):
    """
    Runs the initial Foundry pipeline for all jobs to simulate the AI processing step.
    This will identify ambiguities and create the clarification requests for the user.
    """
    print("\n--- Running initial AI simulation pipeline... ---")
    
    # 1. Define the sequence of operations using our custom phases
    pipeline = build_pipeline(db_session, simulator, threshold)
    
    # 2. Run the pipeline for each job
    for job_id in job_ids:
        pipeline.run(job_id=job_id)

    # 3. Verify the outcome
    clarification_requests_count = db_session.query(Job).filter(Job.status == "pending_clarification").count()
    print(f"--- Pipeline run complete. Found {clarification_requests_count} jobs needing human review. ---")


if __name__ == "__main__":
    # --- 1. GATHER USER CONFIGURATION ---
    print("--- Foundry Production Run Simulator ---")
    
    use_case = questionary.select(
        "Which production run would you like to simulate?",
        choices=["Invoice Processing", "Utility Pole Detection"],
    ).ask()

    if use_case is None: # User pressed Ctrl+C
        exit()

    threshold_str = questionary.text(
        "Enter the confidence threshold for human review (e.g., 0.95):",
        default="0.95",
        validate=lambda text: 0.0 <= float(text) <= 1.0
    ).ask()
    
    if threshold_str is None:
        exit()
    
    confidence_threshold = float(threshold_str)

    # --- 2. SETUP APPLICATION STATE ---
    db = setup_database()
    
    # Select the correct mock data based on user choice
    mock_data = mock_invoice_results if use_case == "Invoice Processing" else mock_pole_detection_results
    ai_simulator = MockAISimulator(mock_data)

    # The AppState object will store our "global" state for the web server
    AppState.db_session = db
    AppState.use_case = use_case
    
    # --- 3. RUN THE SIMULATION ---
    initial_job_ids = create_initial_jobs(db, use_case)
    run_initial_ai_simulation(db, initial_job_ids, ai_simulator, confidence_threshold)

    # --- 4. LAUNCH THE WEB SERVER ---
    print("\n--- Starting web server for human-in-the-loop review. ---")
    print("--- Open http://localhost:8000 in your browser. ---")
    print("--- Press Ctrl+C to stop the server. ---")

    uvicorn.run(app, host="0.0.0.0", port=8000)
