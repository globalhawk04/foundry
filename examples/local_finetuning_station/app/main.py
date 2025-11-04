# FILE: app/main.py (Corrected and Finalized)

import os
import shutil
import zipfile
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from multiprocessing import Process

# --- Application & Foundry Imports ---
from .state import AppState, AppStatus, AppMode
from workers.inference_worker import run_inference
from workers.training_worker import run_training
from foundry.models import Job, FoundryClarificationRequest
from foundry.correction import CorrectionHandler

# --- FastAPI Application Setup ---
app = FastAPI()

# Define the path for user data
DATA_DIR = "data"
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
IMAGE_DIR = os.path.join(DATA_DIR, "images")

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)

# Mount static files and templates AFTER paths are defined
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/images", StaticFiles(directory=IMAGE_DIR), name="images")
templates = Jinja2Templates(directory=["templates", "templates/partials"])

# ==============================================================================
# 1. CORE UI & STATUS ENDPOINTS
# ==============================================================================

@app.get("/", response_class=HTMLResponse)
async def serve_main_page(request: Request):
    """Serves the main single-page application shell."""
    return templates.TemplateResponse("main_page.html", {"request": request})

@app.get("/api/current_view", response_class=HTMLResponse)
async def get_current_view(request: Request):
    """Dynamically serves the correct UI based on the application's state."""
    status = AppState.STATUS
    
    if status == AppStatus.IDLE:
        return templates.TemplateResponse("_idle_view.html", {"request": request})
    elif status == AppStatus.CORRECTION:
        return templates.TemplateResponse("_correction_view.html", {"request": request})
    elif status == AppStatus.PRE_TRAINING:
        return await serve_summary_page(request)
    elif status == AppStatus.TRAINING:
        return templates.TemplateResponse("_training_view.html", {"request": request})
    elif status == AppStatus.COMPLETE:
        return templates.TemplateResponse("_complete_view.html", {"request": request})
    else: # INFERENCE or ERROR
        return templates.TemplateResponse("_status_message.html", {
            "request": request, "status": AppState.STATUS.value, "message": AppState.STATUS_MESSAGE
        })

@app.get("/api/status", response_class=HTMLResponse)
async def get_status_as_html(request: Request):
    """Provides the raw status formatted as a simple HTML partial for polling."""
    status_data = AppState.get_status()
    return templates.TemplateResponse("_status_message.html", {
        "request": request, "status": status_data["status"], "message": status_data["message"]
    })

@app.get("/summary", response_class=HTMLResponse)
async def serve_summary_page(request: Request):
    """Serves the summary page before training begins."""
    from workers.inference_worker import SessionLocal
    db = SessionLocal()
    try:
        total_jobs = db.query(Job).count()
        corrected_jobs = db.query(Job).filter(Job.correction_record != None).count()
        return templates.TemplateResponse("pre_training_summary.html", {
            "request": request, "total_jobs": total_jobs, "corrected_jobs": corrected_jobs
        })
    finally:
        db.close()

# ==============================================================================
# 2. WORKFLOW & CORRECTION ENDPOINTS
# ==============================================================================

@app.post("/upload")
async def handle_upload(zip_file: UploadFile = File(...), threshold: float = Form(...)):
    """Handles data upload, unzips files, and kicks off the inference worker."""
    if AppState.STATUS != AppStatus.IDLE:
        raise HTTPException(status_code=409, detail="System is not ready for upload.")
    if not zip_file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a .zip file.")

    AppState.set_status(AppStatus.INFERENCE, "Processing uploaded files...")
    AppState.MODEL_TYPE = AppMode.OCR

    if os.path.exists(IMAGE_DIR):
        shutil.rmtree(IMAGE_DIR)
    os.makedirs(IMAGE_DIR)
    
    zip_path = os.path.join(UPLOAD_DIR, zip_file.filename)
    with open(zip_path, "wb") as buffer:
        shutil.copyfileobj(zip_file.file, buffer)
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(IMAGE_DIR)
    
    print(f"Unzipped {zip_file.filename} to {IMAGE_DIR}. Kicking off inference worker...")
    p = Process(target=run_inference, args=(IMAGE_DIR, threshold))
    p.start()
    
    return JSONResponse({"message": "Upload successful, inference started."})

@app.get("/api/clarifications/next", response_class=HTMLResponse)
async def get_next_clarification_card(request: Request):
    """Finds the next pending clarification request and renders the OCR review card."""
    from workers.inference_worker import SessionLocal
    db = SessionLocal()
    try:
        next_request = db.query(FoundryClarificationRequest).filter(
            FoundryClarificationRequest.status == "pending"
        ).order_by(FoundryClarificationRequest.id).first()

        if not next_request:
            AppState.set_status(AppStatus.PRE_TRAINING, "Ready for user to start fine-tuning.")
            return HTMLResponse(headers={"HX-Redirect": "/summary"})
        
        return templates.TemplateResponse("_review_ocr_card.html", {
            "request": request, "clarification_request": next_request
        })
    finally:
        db.close()

@app.post("/api/clarifications/{request_id}/resolve", response_class=HTMLResponse)
async def resolve_clarification(request: Request, request_id: int, corrected_text: str = Form(...)):
    """Handles the submission from the OCR correction form."""
    from workers.inference_worker import SessionLocal
    db = SessionLocal()
    try:
        req_to_resolve = db.get(FoundryClarificationRequest, request_id)
        if not req_to_resolve:
            raise HTTPException(status_code=404, detail="Request not found.")
        
        job_id = req_to_resolve.context_data['job_id']
        job = db.get(Job, job_id)
        
        handler = CorrectionHandler(db_session=db)
        
        class OcrSchema:
            def model_json_schema(self): return {'properties': {}}

        form_data = {"text": corrected_text}
        job.corrected_output = {"text": corrected_text, "confidence": 1.0}
        
        # This will create the CorrectionRecord
        handler.save_correction(job_id=job_id, form_data=form_data, schema=OcrSchema())
        
        req_to_resolve.status = "resolved"
        db.commit()
        
        return await get_next_clarification_card(request)
    finally:
        db.close()

@app.post("/train")
async def handle_training_trigger():
    """Kicks off the background training worker process."""
    if AppState.STATUS not in [AppStatus.PRE_TRAINING, AppStatus.COMPLETE]:
        raise HTTPException(status_code=409, detail="System is not in a state to begin training.")

    model_type = AppState.MODEL_TYPE
    AppState.set_status(AppStatus.TRAINING, "Initializing training worker...")

    p = Process(target=run_training, args=(model_type,))
    p.start()

    return JSONResponse({"message": "Training process started."})