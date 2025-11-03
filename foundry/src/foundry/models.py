# FILE: foundry/models.py
#
# This file defines the core, framework-agnostic data models for Foundry.
# We are using SQLAlchemy as our ORM, but the principles can be applied
# to any database-backed system (like the Django ORM).

import datetime
from sqlalchemy import (
    Column, Integer, String, JSON, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship, declarative_base

# In a real project, this Base would be in a shared 'database.py' file.
Base = declarative_base()

# ==============================================================================
# 1. USER MODEL
# A minimal user model to handle ownership of framework objects.
# ==============================================================================

# FILE: src/foundry/models.py (Corrected)

class User(Base):
    """
    Represents a user in the system. Foundry jobs and records are tied to a user.
    """
    __tablename__ = "foundry_users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    
    # Relationships
    jobs = relationship("Job", back_populates="owner", cascade="all, delete-orphan")
    clarification_requests = relationship("FoundryClarificationRequest", back_populates="owner", cascade="all, delete-orphan") # <--- ADD THIS LINE
# ==============================================================================
# 2. CORE FOUNDRY MODELS
# These models form the backbone of the data correction and fine-tuning flywheel.
# ==============================================================================

class Job(Base):
    """
    Represents a single, discrete unit of work for an AI to perform and a human
    to potentially correct. This is the generic abstraction of the original
    project's 'CorrectionQueueItem'.
    """
    __tablename__ = "foundry_jobs"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("foundry_users.id"), nullable=False)

    # Core Job Data
    status = Column(String, default="pending_correction", nullable=False, index=True)
    # Examples: 'pending_correction', 'completed', 'failed', 'in_progress'

    input_data = Column(JSON, nullable=False)
    # Stores the input for the AI. Flexible to handle various types.
    # Example for an image: {"type": "image", "gcs_uri": "gs://bucket/image.jpg"}
    # Example for text: {"type": "text", "content": "The raw text to be processed."}

    initial_ai_output = Column(JSON, nullable=True)
    # The first, potentially flawed, structured output from the AI model.

    corrected_output = Column(JSON, nullable=True)
    # The final, human-verified and corrected structured output. Populated
    # after the user completes a review in the "Correction Deck".
    # --- NEW FIELDS FOR THE RESILIENCE MODULE ---
    pipeline_context = Column(JSON, nullable=True)
    # Stores the intermediate state of a running pipeline.
    
    error_message = Column(Text, nullable=True)
    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="jobs")
    correction_record = relationship("CorrectionRecord", back_populates="job", uselist=False, cascade="all, delete-orphan")

# --- NEW MODEL FOR THIS TASK ---
class FoundryClarificationRequest(Base):
    """
    Stores a single, actionable question from the system to the user, generated
    by an AmbiguityDetector.
    """
    __tablename__ = "foundry_clarification_requests"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("foundry_users.id"), nullable=False)

    request_type = Column(String, nullable=False, index=True)
    # A developer-defined string that identifies the type of question,
    # e.g., "LINK_PRODUCT", "VERIFY_ADDRESS", "CLASSIFY_SENTIMENT".

    status = Column(String, default="pending", nullable=False, index=True)
    # 'pending' or 'resolved'

    context_data = Column(JSON, nullable=False)
    # A JSON blob containing all data needed to ask the question
    # and process the answer. For example, the names of two items to merge,
    # or the text of a customer review.

    resolution_data = Column(JSON, nullable=True)
    # A place to store the user's answer for auditing purposes.
    # e.g., {"answer": "yes", "resolved_at": "2025-09-26T10:00:00Z"}

    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="clarification_requests")

class CorrectionRecord(Base):
    """
    A self-contained, export-ready record representing a single training example
    for fine-tuning. It captures the source input, the model's flawed attempt,
    and the human's "ground truth" correction.
    
    This formalizes the 'final_tuning_record' dictionary from the original project.
    """
    __tablename__ = "foundry_correction_records"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("foundry_jobs.id"), nullable=False, unique=True)
    
    status = Column(String, default="pending_review", nullable=False, index=True)
    # Examples: 'pending_review', 'approved_for_finetuning', 'rejected'

    # The three core components of a fine-tuning example.
    # These are denormalized from the Job model to make this table
    # a self-sufficient, portable dataset.
    
    source_input = Column(JSON, nullable=False)
    # A copy of the Job's 'input_data'.

    model_output = Column(JSON, nullable=False)
    # A copy of the Job's 'initial_ai_output'.

    human_correction = Column(JSON, nullable=False)
    # A copy of the Job's 'corrected_output'.
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    job = relationship("Job", back_populates="correction_record")
