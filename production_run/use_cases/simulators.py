# FILE: examples/production_run/use_cases/simulators.py

import threading
from typing import List, Dict, Any

class MockAISimulator:
    """
    A simple, stateful simulator to mimic the behavior of a real AI model.

    It cycles through a predefined list of prediction results.
    This class is designed to be thread-safe to handle multiple
    concurrent jobs if needed (e.g., in a real web server scenario).
    """
    def __init__(self, predefined_results: List[Dict[str, Any]]):
        """
        Initializes the simulator with a list of results it should return.

        Args:
            predefined_results: A list of dictionaries, where each dictionary
                                represents the structured output of an AI model
                                for a single input.
        """
        if not predefined_results:
            raise ValueError("predefined_results cannot be an empty list.")
        self.results = predefined_results
        self._lock = threading.Lock()
        self._run_count = 0

    def predict(self, input_data: Any) -> Dict[str, Any]:
        """
        Returns the next predefined result in a thread-safe manner.

        The input_data is ignored in this mock implementation, as we are
        simply cycling through results. In a real scenario, this method
        would process the input.

        Returns:
            A dictionary containing the structured AI prediction.
        """
        with self._lock:
            # Cycle through the results using the modulo operator
            result_index = self._run_count % len(self.results)
            result = self.results[result_index]
            self._run_count += 1
            return result
