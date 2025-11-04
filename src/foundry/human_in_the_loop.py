# FILE: foundry/human_in_the_loop.py (Corrected)

from abc import ABC, abstractmethod
from sqlalchemy.orm import Session

from .models import Job, FoundryClarificationRequest
from .pipeline import Phase, PhaseExecutionError

from jinja2 import Environment, PackageLoader, select_autoescape
template_env = Environment(
    loader=PackageLoader("foundry", "templates"),
    autoescape=select_autoescape()
)

# ==============================================================================
# 1. CORE ABSTRACTIONS
# ==============================================================================

class AmbiguityDetector(ABC):
    """
    An abstract base class for detecting issues in a completed job that
    require human clarification.

    Developers will subclass this to implement their own business logic.
    """
    def __init__(self, db_session: Session):
        self.db = db_session

    @abstractmethod
    def detect(self, job: Job) -> list[dict]:
        """
        Analyzes a job and its output to find ambiguities.

        Args:
            job: The completed Job object to analyze.

        Returns:
            A list of dictionaries. Each dictionary contains the data needed
            to create a FoundryClarificationRequest object, specifically:
            - 'request_type': A string identifier for the question type.
            - 'context_data': A JSON-serializable dictionary with all
                              necessary context for the user.
        """
        pass

# ==============================================================================
# 2. PIPELINE INTEGRATION
# ==============================================================================

class HumanInTheLoopPhase(Phase):
    """
    A special pipeline phase that runs an AmbiguityDetector.

    If any clarification requests are generated, it changes the job status
    to 'pending_clarification' and effectively pauses the pipeline.
    """
    def __init__(self, detector_class: type[AmbiguityDetector]):
        """
        Args:
            detector_class: The AmbiguityDetector class (not an instance)
                            to use for detection.
        """
        if not issubclass(detector_class, AmbiguityDetector):
            raise TypeError("detector_class must be a subclass of AmbiguityDetector.")
        self.detector_class = detector_class

    # --- FIX: Updated the method signature to match the new abstract Phase ---
    def process(self, context: dict, db_session: Session) -> dict:
        """
        Executes the ambiguity detection logic.

        Args:
            context: The pipeline context, which must include 'job_id'.
            db_session: The active SQLAlchemy session, provided by the pipeline.

        Returns:
            The original context, unchanged.
        """
        job_id = context.get('job_id')
        
        # --- FIX: Removed dependency on getting db_session from context ---
        if not job_id:
            raise PhaseExecutionError("Context must contain 'job_id'.")

        job = db_session.get(Job, job_id)
        if not job:
            raise PhaseExecutionError(f"Job {job_id} not found.")

        # Instantiate the detector with the session
        detector = self.detector_class(db_session=db_session)
        
        # Run the detection logic
        requests_to_create = detector.detect(job)
        
        if requests_to_create:
            print(f"--- [Job {job_id}] Found {len(requests_to_create)} ambiguities. Pausing pipeline. ---")
            
            # Create the request objects in the database
            for req_data in requests_to_create:
                new_request = FoundryClarificationRequest(
                    owner_id=job.owner_id,
                    request_type=req_data['request_type'],
                    context_data=req_data['context_data']
                )
                db_session.add(new_request)
            
            # Pause the job by setting its status
            job.status = "pending_clarification"
            db_session.commit()
            
        else:
            print(f"--- [Job {job_id}] No ambiguities found. ---")

        return context

# ==============================================================================
# 3. EXAMPLE IMPLEMENTATION
# (This section is unchanged and remains correct)
# ==============================================================================

class UnlinkedProductDetector(AmbiguityDetector):
    """
    An example detector that finds products in a job's output that
    haven't been linked to a canonical pantry item.
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
                        "prompt_for_user": f"The item '{item.get('item_name')}' from invoice #{job.id} needs to be linked to a product in your inventory. Which product is it?"
                    }
                })
        return requests


# ==============================================================================
# 4. CLARIFICATION FEED UI RENDERING
# (This section is unchanged and remains correct)
# ==============================================================================

def render_clarification_feed(db_session: Session, user_id: int) -> str:
    """
    Renders the main container page for the clarification feed.
    """
    template = template_env.get_template("clarification_feed.html")
    return template.render(user_id=user_id)


def get_next_clarification_card(db_session: Session, user_id: int) -> str:
    """
    Finds the next pending clarification request for a user and renders the
    appropriate HTML card for it.
    """
    from sqlalchemy import select
    from .models import FoundryClarificationRequest

    query = select(FoundryClarificationRequest).where(
        FoundryClarificationRequest.owner_id == user_id,
        FoundryClarificationRequest.status == "pending"
    ).order_by(FoundryClarificationRequest.id).limit(1)
    
    next_request = db_session.execute(query).scalars().first()

    if not next_request:
        template = template_env.get_template("partials/_clarification_complete.html")
        return template.render()

    request_type = next_request.request_type
    template_name = f"partials/_clarification_{request_type.lower()}.html"

    try:
        template = template_env.get_template(template_name)
    except Exception:
        template = template_env.get_template("partials/_clarification_unknown.html")

    return template.render(request=next_request)