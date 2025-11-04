# FILE: workers/inference_worker.py

import os
import glob
import torch
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# --- Application & Foundry Imports ---
# We are in a separate process, so we need to set up the path
# to find our app and foundry modules.
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.state import AppState, AppStatus
from app.gpu_lock import GPULock
from foundry.models import Base, Job, User
from foundry.pipeline import Pipeline, Phase, PhaseExecutionError
from foundry.human_in_the_loop import AmbiguityDetector, HumanInTheLoopPhase


# ==============================================================================
# 1. DATABASE SETUP FOR THE WORKER PROCESS
# ==============================================================================
DB_PATH = "data/foundry.db"
engine = create_engine(f"sqlite:///{DB_PATH}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_database():
    """Initializes the database and creates tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


# ==============================================================================
# 2. FOUNDRY PIPELINE DEFINITION
# ==============================================================================

class InferencePhase(Phase):
    """A custom Foundry Phase to run TrOCR inference."""
    def __init__(self, processor, model, device):
        self.processor = processor
        self.model = model
        self.device = device

    def process(self, context: dict, db_session: Session) -> dict:
        job_id = context.get('job_id')
        job = db_session.get(Job, job_id)
        if not job:
            raise PhaseExecutionError(f"Job {job_id} not found.")

        image_path = job.input_data.get("path")
        try:
            image = Image.open(image_path).convert("RGB")
            pixel_values = self.processor(images=image, return_tensors="pt").pixel_values
            pixel_values = pixel_values.to(self.device)

            # Generate token IDs and decode them
            generated_ids = self.model.generate(pixel_values, output_scores=True, return_dict_in_generate=True)
            generated_text = self.processor.batch_decode(generated_ids.sequences, skip_special_tokens=True)[0]
            
            # --- Calculate a simple confidence score ---
            # We use the average log probability of the generated tokens.
            # This is a common way to estimate confidence for generative models.
            scores = generated_ids.scores
            token_probs = torch.stack([score.log_softmax(-1) for score in scores], dim=1)
            generated_tokens = generated_ids.sequences[:, 1:]
            token_log_probs = torch.gather(token_probs, 2, generated_tokens[:, :, None]).squeeze(-1)
            # Filter out padding tokens if any (-100)
            token_log_probs = token_log_probs[generated_tokens != -100]
            avg_log_prob = token_log_probs.mean().item()
            confidence = torch.exp(torch.tensor(avg_log_prob)).item() # Convert log prob back to a probability

            # Save the result to the job
            job.initial_ai_output = {"text": generated_text, "confidence": confidence}
            db_session.commit()
            
        except Exception as e:
            raise PhaseExecutionError(f"Error processing image {image_path}: {e}")

        return context


def build_pipeline(db_session: Session, processor, model, device, threshold: float) -> Pipeline:
    """Factory function to build the inference pipeline."""

    class LowConfidenceDetector(AmbiguityDetector):
        """Flags jobs where the OCR confidence is below the user's threshold."""
        def detect(self, job: Job) -> list[dict]:
            confidence = job.initial_ai_output.get("confidence", 0)
            if confidence < threshold:
                return [{
                    "request_type": "REVIEW_OCR",
                    "context_data": {
                        "job_id": job.id,
                        "image_path": job.input_data.get("path"),
                        "ai_output": job.initial_ai_output
                    }
                }]
            return []

    phases = [
        InferencePhase(processor, model, device),
        HumanInTheLoopPhase(detector_class=LowConfidenceDetector)
    ]
    return Pipeline(db_session=db_session, phases=phases)


# ==============================================================================
# 3. MAIN WORKER FUNCTION
# ==============================================================================

def run_inference(image_dir: str, threshold: float):
    """
    The main function for the inference worker process.
    """
    try:
        AppState.set_status(AppStatus.INFERENCE, "Initializing inference worker...")
        setup_database()
        db = SessionLocal()

        # Clean up the database from any previous run
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

        # Create a default user for this run
        user = User(username="default_user")
        db.add(user)
        db.commit()

        # Find all images and create Foundry Job objects
        image_paths = glob.glob(os.path.join(image_dir, '*'))
        job_ids = []
        for path in image_paths:
            job = Job(owner_id=user.id, status="pending", input_data={"path": path})
            db.add(job)
            db.commit()
            job_ids.append(job.id)
        
        AppState.set_status(AppStatus.INFERENCE, "Downloading AI model...")

        with GPULock(owner="InferenceWorker"):
            device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # --- Load Model & Processor ---
            processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-handwritten')
            # NOTE: We are NOT using quantization here because TrOCR is small enough
            # and inference is fast. Quantization is more critical for training.
            model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-handwritten').to(device)

            # --- Build and Run Pipeline ---
            pipeline = build_pipeline(db, processor, model, device, threshold)
            
            for i, job_id in enumerate(job_ids):
                AppState.set_status(AppStatus.INFERENCE, f"Processing image {i+1} of {len(job_ids)}...")
                pipeline.run(job_id=job_id)
            
            # --- Cleanup GPU Memory ---
            del model
            del processor
            torch.cuda.empty_cache()

        db.close()
        AppState.set_status(AppStatus.CORRECTION, "Inference complete. Ready for user correction.")

    except Exception as e:
        print(f"FATAL ERROR in inference worker: {e}")
        AppState.set_status(AppStatus.ERROR, f"An error occurred during inference: {e}")