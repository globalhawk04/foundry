import http.server
import socketserver
import json
from urllib.parse import parse_qs
from pydantic import BaseModel

# SQLAlchemy imports for database setup
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# --- Import our Foundry Framework components ---
# (Assuming they are in a 'foundry' subdirectory)
from foundry.models import Base, User, Job
from foundry.correction import CorrectionHandler, render_correction_form

# --- 1. Define the Schema for our specific use case ---
# This is what makes the Correction Deck generic. A user of the framework
# would define a schema like this for their own data.
class InvoiceCorrectionSchema(BaseModel):
    supplier_name: str
    invoice_number: str
    invoice_date: str
    
    class InventoryItem(BaseModel):
        item_name: str
        total_quantity: float
        total_unit: str
        total_cost: float
        
    inventory_items: list[InventoryItem]

# --- 2. Database and Application Setup ---
DB_FILE = "foundry_quickstart.db"
engine = create_engine(f"sqlite:///{DB_FILE}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Global handler instance for the server to use
db_session = SessionLocal()
correction_handler = CorrectionHandler(db_session)

def setup_database_and_job():
    """Initializes the database and simulates a pre-existing AI job."""
    print("--- Setting up the SQLite database... ---")
    Base.metadata.create_all(bind=engine)
    
    # Check if a job already exists
    job = db_session.get(Job, 1)
    if job:
        print("--- Database already contains a job. ---")
        return

    print("--- Simulating a new AI Job... ---")
    # Create a dummy user
    user = User(username="default_user")
    db_session.add(user)
    
    # This simulates the state *after* an AI has run and produced flawed output.
    simulated_job = Job(
        id=1,
        owner=user,
        status="pending_correction",
        input_data={
            "type": "image",
            "uri": "/static/example_invoice.jpeg", # Path to the image
            "display_template": "partials/_display_image.html"
        },
        initial_ai_output={
            "supplier_name": "Lone Star Provisins Inc.", # <-- TYPO
            "invoice_number": "785670",
            "invoice_date": "2025-08-20",
            "inventory_items": [
                {"item_name": "TAVERN HAM WH", "total_quantity": 15.82, "total_unit": "LB", "total_cost": 87.80},
                {"item_name": "ONIONS YELLOW JBO", "total_quantity": 5, "total_unit": "LB", "total_cost": 35.50} # <-- WRONG QUANTITY
            ]
        }
    )
    db_session.add(simulated_job)
    db_session.commit()
    print("--- Job #1 created and saved. ---")

# --- 3. A Minimal Web Server to Host the UI ---
class FoundryHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """A simple request handler to serve the UI and process the form."""

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            
            # Fetch the job and render the correction form
            job = db_session.get(Job, 1)
            html_content = render_correction_form(job, InvoiceCorrectionSchema)
            self.wfile.write(bytes(html_content, "utf8"))
        else:
            # For any other path (like /static/image.jpg), serve the file directly
            super().do_GET()

    def do_POST(self):
        if self.path == "/save":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            # parse_qs correctly handles form fields with '[]'
            form_data = parse_qs(post_data.decode('utf-8'))
            
            # Use our handler to save the correction
            correction_handler.save_correction(job_id=1, form_data=form_data, schema=InvoiceCorrectionSchema)
            
            # Respond with a simple success message
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Correction Saved Successfully!</h1><p>You can now close this tab and stop the server in your terminal (Ctrl+C).</p>")

# --- 4. Main Execution Block ---
if __name__ == "__main__":
    setup_database_and_job()
    
    PORT = 8000
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), FoundryHTTPRequestHandler) as httpd:
        print(f"\n--- Foundry Quickstart Server running at http://localhost:{PORT} ---")
        print("--- Open the URL in your browser to use the Correction Deck. ---")
        print("--- Press Ctrl+C to stop the server and complete the flywheel. ---")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n--- Server stopped. ---")

    # --- 5. The Final Step of the Flywheel: Exporting Data ---
    print("\n--- Exporting approved corrections to fine-tuning format... ---")
    jsonl_data = correction_handler.export_records()
    
    if jsonl_data:
        with open("corrected_data.jsonl", "w") as f:
            f.write(jsonl_data)
        print("--- Data successfully exported to 'corrected_data.jsonl' ---")
        print("\n--- QUICKSTART COMPLETE ---")
    else:
        print("--- No corrections were approved for export. ---")
        
    db_session.close()
