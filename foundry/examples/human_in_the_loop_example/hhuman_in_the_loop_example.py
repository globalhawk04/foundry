# FILE: examples/human_in_the_loop_example.py

import http.server
import socketserver
import json
from urllib.parse import parse_qs

# SQLAlchemy imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# --- Import Foundry Framework components ---
from foundry.models import Base, User, Job, FoundryClarificationRequest
from foundry.pipeline import Pipeline, Phase, PhaseExecutionError
from foundry.human_in_the_loop import (
    AmbiguityDetector, 
    HumanInTheLoopPhase,
    render_clarification_feed,
    get_next_clarification_card
)

# --- 1. APPLICATION-SPECIFIC IMPLEMENTATIONS ---
# A developer using Foundry would define classes like these for their specific domain.

class UnlinkedProductDetector(AmbiguityDetector):
    """
    Finds products in a job's output that haven't been linked to a canonical inventory item.
    (Copied from Task 3.1 for a self-contained example)
    """
    def detect(self, job: Job) -> list[dict]:
        requests = []
        ai_output = job.initial_ai_output or {}
        
        for item in ai_output.get("inventory_items", []):
            if item.get("linked_pantry_item_id") is None:
                requests.append({
                    "request_type": "LINK_PRODUCT",
                    "context_data": {
                        "item_name_from_invoice": item.get("item_name"),
                        "job_id": job.id,
                        "prompt_for_user": f"The item '{item.get('item_name')}' from invoice job #{job.id} needs to be linked to an existing product. Which product is it?"
                    }
                })
        return requests

class FinalProcessingPhase(Phase):
    """A placeholder for what would happen *after* human clarification."""
    def process(self, context: dict) -> dict:
        print("--- Final processing phase is running after human intervention! ---")
        # In a real app, this might calculate final costs, update inventory, etc.
        context['final_result'] = "Human feedback successfully incorporated."
        return context

# --- 2. DATABASE AND APPLICATION SETUP ---
DB_FILE = "foundry_hitl_example.db"
engine = create_engine(f"sqlite:///{DB_FILE}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_database_and_job():
    """Initializes the DB and creates a Job with an ambiguous AI output."""
    print("--- Setting up the database... ---")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Check if we've already set up
    if db.get(Job, 1):
        print("--- Database already contains a job. ---")
        return

    print("--- Creating a simulated user and a job with ambiguous AI output... ---")
    user = User(username="test_user")
    
    # This job has completed an initial pipeline, but its output is flawed.
    job_with_ambiguity = Job(
        id=1,
        owner=user,
        status="completed_phase:InitialExtraction",
        input_data={"file": "invoice123.pdf"},
        initial_ai_output={
            "supplier_name": "Sysco",
            "inventory_items": [
                {"item_name": "TAVERN HAM WH", "linked_pantry_item_id": 101},
                {"item_name": "ONIONS YELLOW JBO", "linked_pantry_item_id": None} # <-- THE AMBIGUITY
            ]
        }
    )
    db.add(job_with_ambiguity)
    db.commit()
    db.close()
    print("--- Job #1 created. ---")

def run_ambiguity_detection_pipeline():
    """Runs a pipeline that is designed to find and flag ambiguities."""
    db = SessionLocal()
    print("\n--- Running the Ambiguity Detection Pipeline for Job #1... ---")
    
    # This pipeline's only job is to run the detector.
    detection_pipeline = Pipeline(db, phases=[
        HumanInTheLoopPhase(detector_class=UnlinkedProductDetector)
    ])
    
    # We need to pass the job_id and db_session in the initial context for this phase
    job = db.get(Job, 1)
    job.pipeline_context = {"job_id": 1, "db_session": db}
    db.commit()

    detection_pipeline.run(job_id=1)

    # Verify the outcome
    job = db.get(Job, 1)
    print(f"--- Pipeline finished. Job status is now: '{job.status}' ---") # Should be 'pending_clarification'
    db.close()


# --- 3. A MINIMAL WEB SERVER TO HOST THE CLARIFICATION FEED ---
class FoundryHITLRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        db = SessionLocal()
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            # Serve the main container page
            html_content = render_clarification_feed(db, user_id=1)
            self.wfile.write(bytes(html_content, "utf8"))
        elif self.path == "/clarifications/next":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            # Serve the next question card
            html_content = get_next_clarification_card(db, user_id=1)
            self.wfile.write(bytes(html_content, "utf8"))
        else:
            self.send_error(404, "Not Found")
        db.close()
        
    def do_POST(self):
        # Path should be like /clarifications/1/resolve
        if self.path.startswith("/clarifications/") and self.path.endswith("/resolve"):
            db = SessionLocal()
            try:
                request_id = int(self.path.split('/')[-2])
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                form_data = parse_qs(post_data.decode('utf-8'))
                
                print(f"\n--- Received resolution for request #{request_id} with data: {form_data} ---")

                # --- RESOLVE THE REQUEST ---
                req_to_resolve = db.get(FoundryClarificationRequest, request_id)
                if req_to_resolve:
                    req_to_resolve.status = "resolved"
                    req_to_resolve.resolution_data = {"user_answer": form_data}
                    
                    # --- UN-PAUSE THE JOB ---
                    job_id = req_to_resolve.context_data['job_id']
                    job = db.get(Job, job_id)
                    job.status = "ready_for_final_processing" # Update status
                    db.commit()
                    print(f"--- Request #{request_id} resolved. Job #{job.id} is now '{job.status}'. ---")

                # Respond by telling the browser to trigger the event that loads the next card
                self.send_response(200)
                self.send_header("HX-Trigger", "resolutionComplete")
                self.end_headers()
                
            finally:
                db.close()
        else:
            self.send_error(404, "Not Found")

# --- 4. MAIN EXECUTION BLOCK ---
if __name__ == "__main__":
    setup_database_and_job()
    run_ambiguity_detection_pipeline()
    
    PORT = 8000
    with socketserver.TCPServer(("", PORT), FoundryHITLRequestHandler) as httpd:
        print(f"\n--- Human-in-the-Loop server running at http://localhost:{PORT} ---")
        print("--- Open the URL in your browser to answer the clarification question. ---")
        print("--- After resolving, press Ctrl+C to stop the server. ---")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n--- Server stopped. ---")

    # --- 5. VERIFICATION ---
    db = SessionLocal()
    final_job_state = db.get(Job, 1)
    print(f"\n--- Final Job Status: {final_job_state.status} ---")
    request = db.query(FoundryClarificationRequest).first()
    print(f"--- Final Request Status: {request.status} ---")
    print(f"--- User's Answer was: {request.resolution_data} ---")
    db.close()
    print("\n--- HUMAN-IN-THE-LOOP EXAMPLE COMPLETE ---")
