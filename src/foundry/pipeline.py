# FILE: foundry/pipeline.py (Corrected)

import json
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from .models import Job # Assumes models.py is in the same package

# ==============================================================================
# 1. CORE ABSTRACTIONS
# ==============================================================================

class PhaseExecutionError(Exception):
    """Custom exception for errors that occur during a Phase's execution."""
    pass

class Phase(ABC):
    """
    An abstract base class representing a single, synchronous step in a Pipeline.

    Each subclass must implement the `process` method.
    """
    @property
    def name(self) -> str:
        """A unique, descriptive name for this phase."""
        return self.__class__.__name__

    @abstractmethod
    def process(self, context: dict, db_session: Session) -> dict:
        """
        The core logic of the phase. It receives the current pipeline context,
        performs its operations, and returns the updated context.

        Args:
            context: A dictionary containing the current state of the pipeline.
            db_session: The active SQLAlchemy session for any database operations.

        Returns:
            The updated context dictionary.

        Raises:
            PhaseExecutionError: If the phase encounters a critical error.
        """
        pass

class Pipeline:
    """
    An orchestrator that runs a sequence of Phase objects, ensuring resilience
    by persisting the state after each successful step.
    """
    def __init__(self, db_session: Session, phases: list[Phase]):
        """
        Args:
            db_session: The SQLAlchemy session for database operations.
            phases: An ordered list of Phase instances to execute.
        """
        if not all(isinstance(p, Phase) for p in phases):
            raise TypeError("All items in the 'phases' list must be instances of the Phase class.")
        self.db = db_session
        self.phases = phases

    def run(self, job_id: int):
        """
        Executes the pipeline for a given job.

        Args:
            job_id: The ID of the Job to process.
        """
        job = self.db.get(Job, job_id)
        if not job:
            print(f"PIPELINE ERROR: Job {job_id} not found.")
            return

        # Initialize context from the job's stored context or its input data
        context = job.pipeline_context or job.input_data

        job.status = "in_progress"
        self.db.commit()

        for phase in self.phases:
            try:
                print(f"--- [Job {job_id}] Running Phase: {phase.name} ---")
                
                # --- FIX: Pass the db_session as an explicit argument ---
                # This ensures the context dictionary only ever contains serializable data.
                context = phase.process(context, db_session=self.db)
                
                # --- RESILIENCE CHECKPOINT ---
                # The state is saved to the database *after* each phase succeeds.
                job.pipeline_context = context
                job.status = f"completed_phase:{phase.name}"
                flag_modified(job, "pipeline_context") # Necessary for JSON mutation
                self.db.commit()
                print(f"--- [Job {job_id}] Phase '{phase.name}' Succeeded. State saved. ---")

            except PhaseExecutionError as e:
                print(f"--- [Job {job_id}] FATAL ERROR in Phase '{phase.name}': {e} ---")
                job.status = "failed"
                job.error_message = str(e)
                self.db.commit()
                # Stop the pipeline on the first failure
                return

        # If all phases complete successfully
        job.status = "completed"
        job.initial_ai_output = context # Save the final result to the main output field
        self.db.commit()
        print(f"--- [Job {job_id}] Pipeline finished successfully. ---")

# ==============================================================================
# 2. EXAMPLE IMPLEMENTATION
# This shows how a developer would use the framework.
# ==============================================================================

class ExtractTextPhase(Phase):
    """An example Phase that extracts text from the initial context."""
    # --- FIX: Updated method signature to match the abstract class ---
    def process(self, context: dict, db_session: Session) -> dict:
        text_content = context.get("content")
        if not text_content:
            raise PhaseExecutionError("Input context must contain a 'content' key with text.")
        
        # In a real scenario, this would involve an AI call. Here, we just log it.
        print(f"Extracting text: '{text_content[:30]}...'")
        context['extracted_text'] = text_content
        return context

class ConvertToUppercasePhase(Phase):
    """An example Phase that transforms the extracted text to uppercase."""
    # --- FIX: Updated method signature to match the abstract class ---
    def process(self, context: dict, db_session: Session) -> dict:
        extracted_text = context.get("extracted_text")
        if not extracted_text:
            raise PhaseExecutionError("Context is missing 'extracted_text' from the previous phase.")
            
        context['uppercased_text'] = extracted_text.upper()
        return context

def run_example_pipeline(db: Session, job: Job):
    """A function that defines and runs a simple pipeline."""
    
    # 1. Define the sequence of operations
    my_phases = [
        ExtractTextPhase(),
        ConvertToUppercasePhase()
    ]
    
    # 2. Instantiate the pipeline
    pipeline = Pipeline(db_session=db, phases=my_phases)
    
    # 3. Run it
    pipeline.run(job_id=job.id)