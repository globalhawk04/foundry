# FILE: examples/production_run/app/schemas.py

from pydantic import BaseModel, Field
from typing import List, TypeVar, Generic, Tuple

# ==============================================================================
# 1. GENERIC & REUSABLE COMPONENTS
# ==============================================================================

# Define a generic TypeVar to allow ConfidenceField to wrap any type (str, float, etc.)
T = TypeVar('T')

class ConfidenceField(BaseModel, Generic[T]):
    """
    A generic Pydantic model to wrap a value with its associated confidence score.
    This provides a standardized structure for any piece of data extracted by the AI.
    """
    value: T
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="The AI's confidence in the correctness of the value, from 0.0 to 1.0"
    )


# ==============================================================================
# 2. INVOICE PROCESSING USE CASE
# ==============================================================================

class LineItem(BaseModel):
    """
    Represents a single line item extracted from an invoice.
    Each field is a ConfidenceField, capturing the AI's uncertainty.
    """
    item_description: ConfidenceField[str]
    quantity: ConfidenceField[float]
    unit_price: ConfidenceField[float]
    total_cost: ConfidenceField[float]


class InvoiceSchema(BaseModel):
    """
    Defines the complete, structured data for a processed invoice.
    This schema is used for the 'initial_ai_output' and 'corrected_output'
    fields in a Foundry Job object.
    """
    supplier_name: ConfidenceField[str]
    invoice_date: ConfidenceField[str]
    invoice_number: ConfidenceField[str]
    line_items: List[LineItem] = []


# ==============================================================================
# 3. UTILITY POLE DETECTION USE CASE
# ==============================================================================

class BoundingBox(BaseModel):
    """
    Represents a single detected object in an image.
    """
    box_id: str = Field(..., description="A unique identifier for this box within the image.")
    label: str = Field(..., description="The predicted label for the object (e.g., 'utility_pole').")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="The AI's confidence that the label is correct for this box."
    )
    # A tuple is used to enforce that there are always exactly 4 coordinate points.
    box: Tuple[int, int, int, int] = Field(
        ...,
        description="The bounding box coordinates in [x_min, y_min, x_max, y_max] format."
    )


class PoleDetectionSchema(BaseModel):
    """
    Defines the complete, structured data for a processed image for pole detection.
    This schema contains a list of all bounding boxes found in the image.
    """
    boxes: List[BoundingBox] = []
