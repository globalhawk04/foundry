# FILE: foundry/correction.py (EXPANDED)

import json
from collections import defaultdict

from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from jinja2 import Environment, PackageLoader, select_autoescape
template_env = Environment(
    loader=PackageLoader("foundry", "templates"), # Look inside the 'foundry' package for a 'templates' directory
    autoescape=select_autoescape()
)

from .models import Job, CorrectionRecord

# In a real app, the Jinja2 environment would be configured once.
template_env = Environment(
    loader=PackageLoader("foundry", "templates"),
    autoescape=select_autoescape()
)

# ==============================================================================
# FORM PARSING UTILITY
# ==============================================================================

def _parse_form_to_dict(form_data: dict, schema: BaseModel) -> dict:
    """
    Parses a flat form submission into a nested dictionary that matches the
    provided Pydantic schema.

    Handles simple key-value pairs and complex list-of-objects structures
    (e.g., 'inventory_items_item_name[]').
    """
    parsed_data = {}
    schema_def = schema.model_json_schema()['properties']
    
    # A temporary structure to reconstruct lists of items
    # Format: { 'list_name': { 0: {'field1': 'valA'}, 1: {'field1': 'valB'} } }
    item_lists = defaultdict(lambda: defaultdict(dict))

    for key, value in form_data.items():
        # Check if this key represents an item in a list
        # e.g., "inventory_items_item_name[]"
        if key.endswith('[]'):
            parts = key.removesuffix('[]').split('_')
            list_name = parts[0]
            field_name = "_".join(parts[1:])
            
            # The form submits multiple values for the same key name
            # So, 'value' here is actually a list of all submitted values
            for index, single_value in enumerate(value):
                item_lists[list_name][index][field_name] = single_value
        
        # Handle simple, top-level fields
        elif key in schema_def:
            parsed_data[key] = value

    # Convert the reconstructed lists into the final format
    for list_name, items in item_lists.items():
        # Sort by index and take only the dictionary values
        parsed_data[list_name] = [items[i] for i in sorted(items.keys())]

    # Perform type casting based on the schema (e.g., string '5.99' -> float 5.99)
    # This is a simplified example; a production version would be more robust.
    for key, prop in schema_def.items():
        if prop.get('type') == 'number' and key in parsed_data:
            try:
                parsed_data[key] = float(parsed_data[key])
            except (ValueError, TypeError):
                parsed_data[key] = 0.0
        elif prop.get('type') == 'array':
            sub_props = prop.get('items', {}).get('properties', {})
            for item in parsed_data.get(key, []):
                for sub_key, sub_prop in sub_props.items():
                    if sub_prop.get('type') == 'number' and sub_key in item:
                        try:
                            item[sub_key] = float(item[sub_key])
                        except (ValueError, TypeError):
                            item[sub_key] = 0.0
                            
    return parsed_data

# ==============================================================================
# CORRECTION HANDLER CLASS
# ==============================================================================

class CorrectionHandler:
    """
    Handles the business logic for saving and exporting corrections.
    """
    def __init__(self, db_session: Session):
        self.db = db_session

    def save_correction(self, job_id: int, form_data: dict, schema: BaseModel) -> Job:
        """
        Parses form data, updates a Job, and creates a CorrectionRecord.

        Args:
            job_id: The ID of the Job being corrected.
            form_data: The raw, flat dictionary from the form submission.
            schema: The Pydantic schema used to structure the correction.

        Returns:
            The updated Job object.
        """
        # 1. Fetch the original job
        job = self.db.get(Job, job_id)
        if not job:
            raise ValueError(f"Job with ID {job_id} not found.")

        # 2. Parse the flat form data into a structured dictionary
        corrected_data = _parse_form_to_dict(form_data, schema)

        # 3. Update the Job with the corrected output and new status
        job.corrected_output = corrected_data
        job.status = "completed"
        
        # 4. Create the definitive CorrectionRecord for fine-tuning
        # First, check if a record already exists to avoid duplicates
        existing_record = self.db.execute(
            select(CorrectionRecord).where(CorrectionRecord.job_id == job_id)
        ).scalars().first()
        
        if existing_record:
            record = existing_record
        else:
            record = CorrectionRecord(job=job)
            
        record.source_input = job.input_data
        record.model_output = job.initial_ai_output
        record.human_correction = job.corrected_output
        record.status = "approved_for_finetuning"
        
        self.db.add(job)
        self.db.add(record)
        self.db.commit()
        self.db.refresh(job)
        
        return job

    def export_records(self, status: str = "approved_for_finetuning") -> str:
        """
        Exports CorrectionRecords into a JSONL format suitable for fine-tuning.

        Args:
            status: The status of records to export.

        Returns:
            A string containing the JSONL data.
        """
        query = select(CorrectionRecord).where(CorrectionRecord.status == status)
        records_to_export = self.db.execute(query).scalars().all()
        
        output_lines = []
        for record in records_to_export:
            # Build the input part for the user's prompt
            user_parts = []
            if record.source_input.get("type") == "image":
                user_parts.append({
                    "fileData": {
                        "mimeType": "image/jpeg",
                        "fileUri": record.source_input.get("uri")
                    }
                })
            elif record.source_input.get("type") == "text":
                 user_parts.append({"text": record.source_input.get("content")})

            # Add a generic instruction
            user_parts.append({"text": "Extract the key business data from the provided input."})

            # Build the final conversational turn
            tuning_record = {
                "contents": [
                    {"role": "user", "parts": user_parts},
                    {"role": "model", "parts": [
                        {"text": json.dumps(record.human_correction)}
                    ]}
                ]
            }
            output_lines.append(json.dumps(tuning_record))
        
        return "\n".join(output_lines)

# FILE: src/foundry/correction.py (Replace the function with this)

# The new, correct function
def render_correction_form(job: Job, schema: BaseModel) -> str:
    """
    Renders the main correction deck HTML for a given job and schema.
    """
    template = template_env.get_template("review_deck.html")

    # --- THIS IS THE FIX ---
    # Manually create a simple dictionary from the job object.
    # This dictionary IS JSON serializable.
    job_context = {
        "id": job.id,
        "status": job.status,
        "input_data": job.input_data,
        # Note: We don't pass the full ai_output here to avoid redundancy
    }

    context = {
        "job": job_context, # Pass the simple dictionary, not the object
        "ai_output": job.initial_ai_output or {},
        "schema_definition": schema.model_json_schema()
    }

    return template.render(context)