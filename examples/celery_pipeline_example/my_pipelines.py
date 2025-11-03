# FILE: my_pipelines.py

from foundry.pipeline import Pipeline, Phase, PhaseExecutionError

# Define your custom phases
class ExtractTextPhase(Phase):
    def process(self, context: dict) -> dict:
        text_content = context.get("content")
        if not text_content:
            raise PhaseExecutionError("Input context must contain a 'content' key.")
        context['extracted_text'] = text_content
        return context

class ConvertToUppercasePhase(Phase):
    def process(self, context: dict) -> dict:
        extracted_text = context.get("extracted_text")
        if not extracted_text:
            raise PhaseExecutionError("Context is missing 'extracted_text'.")
        context['uppercased_text'] = extracted_text.upper()
        return context

# Define your custom pipeline class
class UppercasePipeline(Pipeline):
    def __init__(self, db_session):
        # The sequence of phases is defined here
        phases = [
            ExtractTextPhase(),
            ConvertToUppercasePhase()
        ]
        super().__init__(db_session=db_session, phases=phases)
