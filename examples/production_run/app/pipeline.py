# FILE: examples/production_run/app/pipeline.py

from sqlalchemy.orm import Session

# --- Foundry Framework Imports ---
from foundry.pipeline import Pipeline, Phase, PhaseExecutionError
from foundry.human_in_the_loop import AmbiguityDetector, HumanInTheLoopPhase
from foundry.models import Job, FoundryClarificationRequest

# --- Use Case & Simulator Imports ---
from use_cases.simulators import MockAISimulator


class AIExtractionPhase(Phase):
    """
    A pipeline phase that runs the mock AI simulator and saves its output.
    """
    def __init__(self, simulator: MockAISimulator):
        self.simulator = simulator

    def process(self, context: dict, db_session: Session) -> dict:
        """
        Fetches the job, runs the AI prediction, and saves the initial output.
        """
        job_id = context.get('job_id')
        if not job_id:
            raise PhaseExecutionError("Context must contain 'job_id'.")

        job = db_session.get(Job, job_id)
        if not job:
            raise PhaseExecutionError(f"Job {job_id} not found in AIExtractionPhase.")

        # In a real application, you would pass job.input_data to the model.
        # Here, our simulator just cycles through predefined results.
        ai_prediction = self.simulator.predict(job.input_data)

        # The initial, potentially flawed output is saved to the job.
        # This is critical, as the next phase's AmbiguityDetector will query
        # this field directly from the Job object.
        job.initial_ai_output = ai_prediction
        db_session.commit()
        
        # We pass the prediction along in the context as well.
        context['ai_result'] = ai_prediction
        return context


def build_pipeline(db_session: Session, simulator: MockAISimulator, threshold: float) -> Pipeline:
    """
    A factory function to construct the complete Foundry pipeline.

    This function defines a custom AmbiguityDetector class within its scope
    to give it access to the user-defined 'threshold' value.
    """

    class LowConfidenceDetector(AmbiguityDetector):
        """
        An AmbiguityDetector that finds any field in the AI output with a
        confidence score below the configured threshold.
        """
        def detect(self, job: Job) -> list[dict]:
            """
            Analyzes the job's initial_ai_output and creates clarification requests.
            """
            ai_output = job.initial_ai_output or {}
            found_low_confidence = False

            # --- Check logic for Invoice Schema ---
            if "supplier_name" in ai_output:
                for key, data in ai_output.items():
                    if isinstance(data, dict) and 'confidence' in data:
                        if data['confidence'] < threshold:
                            found_low_confidence = True
                            break
                    elif isinstance(data, list): # Check line_items
                        for item in data:
                            for field, value in item.items():
                                if isinstance(value, dict) and 'confidence' in value:
                                    if value['confidence'] < threshold:
                                        found_low_confidence = True
                                        break
                            if found_low_confidence: break
                
                if found_low_confidence:
                    return [{
                        "request_type": "REVIEW_INVOICE",
                        "context_data": {
                            "job_id": job.id,
                            "image_url": job.input_data.get("url"),
                            "ai_output": job.initial_ai_output
                        }
                    }]

            # --- Check logic for Pole Detection Schema ---
            elif "boxes" in ai_output:
                for box in ai_output.get("boxes", []):
                    if box.get("confidence", 1.0) < threshold:
                        found_low_confidence = True
                        break
                
                if found_low_confidence:
                    return [{
                        "request_type": "REVIEW_POLES",
                        "context_data": {
                            "job_id": job.id,
                            "image_url": job.input_data.get("url"),
                            "ai_output": job.initial_ai_output
                        }
                    }]

            return [] # No low confidence fields found

    # Define the sequence of phases for the pipeline
    phases = [
        AIExtractionPhase(simulator),
        HumanInTheLoopPhase(detector_class=LowConfidenceDetector)
    ]

    return Pipeline(db_session=db_session, phases=phases)
