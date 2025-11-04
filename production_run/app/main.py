# FILE: examples/production_run/app/main.py

from fastapi import FastAPI, Request, Form, Body
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import select

# --- Foundry & Application Imports ---
from foundry.models import Job, FoundryClarificationRequest
from foundry.correction import CorrectionHandler
from app.schemas import InvoiceSchema, PoleDetectionSchema # For form parsing


# = A simple class to hold shared state for the application.
# The 'production_run.py' script will populate these fields before starting the server.
class AppState:
    db_session: Session = None
    use_case: str = None


# --- FastAPI Application Setup ---
app = FastAPI()

# Mount the 'static' directory to serve images, css, js
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup Jinja2 for HTML templating
templates = Jinja2Templates(directory=["templates", "templates/partials"])

# ==============================================================================
# 1. CORE UI ENDPOINTS
# ==============================================================================

@app.get("/", response_class=HTMLResponse)
async def serve_clarification_feed(request: Request):
    """
    Serves the main container page for the Human-in-the-Loop UI.
    This page will use HTMX to fetch the first clarification card.
    """
    return templates.TemplateResponse("clarification_feed.html", {"request": request})


@app.get("/report", response_class=HTMLResponse)
async def serve_final_report(request: Request):
    """
    Serves the final summary page showing the status of all jobs in the run.
    """
    jobs = AppState.db_session.query(Job).order_by(Job.id).all()
    # Check if a job was manually corrected by seeing if it has a correction_record
    job_data = [{
        "id": job.id,
        "status": job.status,
        "input_url": job.input_data.get("url"),
        "was_corrected": job.correction_record is not None
    } for job in jobs]
    
    return templates.TemplateResponse("report.html", {
        "request": request,
        "jobs": job_data,
        "use_case": AppState.use_case
    })


# ==============================================================================
# 2. API ENDPOINTS (for HTMX/JavaScript interaction)
# ==============================================================================

@app.get("/api/clarifications/next", response_class=HTMLResponse)
async def get_next_clarification_card(request: Request):
    """
    Finds the next pending clarification request and renders the appropriate
    HTML partial for it (either invoice or pole detection).
    """
    db = AppState.db_session
    
    # Find the first available request that needs human review
    query = select(FoundryClarificationRequest).where(
        FoundryClarificationRequest.status == "pending"
    ).order_by(FoundryClarificationRequest.id).limit(1)
    next_request = db.execute(query).scalars().first()

    if not next_request:
        # If no requests are left, show a completion message that links to the report
        return templates.TemplateResponse("partials/_clarification_complete.html", {"request": request})

    # Determine which UI to render based on the request type set in the pipeline
    request_type = next_request.request_type
    if request_type == "REVIEW_INVOICE":
        template_name = "partials/_clarification_invoice.html"
    elif request_type == "REVIEW_POLES":
        template_name = "partials/_clarification_pole.html"
    else:
        return HTMLResponse("Error: Unknown request type.", status_code=500)

    return templates.TemplateResponse(template_name, {
        "request": request,
        "clarification_request": next_request
    })


@app.post("/api/clarifications/{request_id}/resolve", response_class=HTMLResponse)
async def resolve_clarification(request: Request, request_id: int):
    """
    Handles the submission from a correction UI.
    It saves the correction and marks the request as resolved.
    This endpoint is flexible and handles both form data (invoices) and JSON (poles).
    """
    db = AppState.db_session
    req_to_resolve = db.get(FoundryClarificationRequest, request_id)
    if not req_to_resolve:
        return HTMLResponse("Error: Request not found.", status_code=404)
        
    job_id = req_to_resolve.context_data['job_id']
    handler = CorrectionHandler(db_session=db)
    
    # --- Process correction based on content type ---
    content_type = request.headers.get('content-type')
    
    if "application/json" in content_type:
        # For pole detection, we expect a JSON body from the JS editor
        corrected_data = await request.json()
        schema = PoleDetectionSchema
        # The JS will send a simplified structure, so we need to wrap it
        # to match the schema our handler expects for parsing.
        # This is a good example of an anti-corruption layer.
        form_data_for_handler = {"boxes": corrected_data.get("boxes", [])}
    else:
        # For invoices, we expect standard form data
        form_data = await request.form()
        schema = InvoiceSchema
        # The correction handler's utility can parse the form directly
        form_data_for_handler = form_data
    
    # --- Use Foundry's CorrectionHandler to save the data ---
    handler.save_correction(job_id=job_id, form_data=form_data_for_handler, schema=schema)
    
    # --- Mark the request as resolved ---
    req_to_resolve.status = "resolved"
    req_to_resolve.resolution_data = {"resolved_by": "user"} # Simple audit trail
    db.commit()

    # Respond with an empty 200 OK, but with a special HTMX header
    # that tells the browser to trigger a GET to load the next card.
    return HTMLResponse(content="", status_code=200, headers={"HX-Trigger": "loadNextCard"})


@app.post("/api/export")
async def export_corrections():
    """
    Exports all approved CorrectionRecords to a JSONL file for download.
    """
    handler = CorrectionHandler(db_session=AppState.db_session)
    jsonl_data = handler.export_records()
    
    return StreamingResponse(
        iter([jsonl_data]),
        media_type="application/jsonl",
        headers={"Content-Disposition": "attachment; filename=corrected_data.jsonl"}
    )
