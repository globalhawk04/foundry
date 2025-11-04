---

# Foundry: The Framework for Production-Grade AI Data Flywheels

**Go from a fragile AI prototype to a resilient, self-improving system.**

Foundry is a Python framework for building production-grade, human-in-the-loop systems that turn daily operations into a scalable, ever-improving data generation engine for fine-tuning your AI models.

---

## The Problem: Moving Beyond the Notebook

Building a simple AI prototype is easy. Building a robust, production-ready AI system that continuously improves is incredibly hard. Real-world AI systems face constant challenges that POCs and notebooks ignore:

*   **Imperfect Models:** Generative AI models are powerful but are never 100% accurate. Their outputs require validation, and forcing them to guess leads to low-quality results and a poor user experience.
*   **Fragile Pipelines:** Real-world AI tasks are multi-step processes. A failure in one OCR or data extraction step shouldn't bring down the entire system or lose valuable, expensive work from prior steps.
*   **Data Ambiguity:** Sometimes, the AI doesn't have enough context to make a confident decision. The system needs a way to pause and ask a human for the specific information it needs to proceed.
*   **Stagnant Models:** An AI model that doesn't learn from its mistakes will never get better. Manually curating datasets from production logs is tedious, error-prone, and rarely gets done.

## The Solution: The Foundry Data Flywheel

Foundry provides the architectural components to solve these problems by helping you build a **data flywheel**: a virtuous cycle where every human correction directly contributes to a better, more accurate, and more autonomous next-generation AI model.

1.  **Resilient Pipelines:** Structure your AI tasks as a series of resilient `Phases`. If a step fails or needs clarification, the pipeline pauses, preserving the work from successful prior steps.
2.  **Human-in-the-Loop:** When the system detects ambiguity (based on confidence scores or custom business logic), it automatically generates a `ClarificationRequest`, pausing the pipeline to ask a human operator for the specific information it needs.
3.  **Correction & Fine-Tuning:** All AI outputs can be reviewed and corrected by a human in a UI. Foundry is UI-agnostic, supporting everything from simple web forms to complex bounding box editors. Every correction is saved as a high-quality `CorrectionRecord`.
4.  **Export & Improve:** The collected `CorrectionRecord`s are exported into a perfect, model-ready `.jsonl` dataset. Use this data to fine-tune your next model, deploy it, and watch the flywheel spin faster with less need for human intervention.

---

## See Foundry in Action in 2 Minutes

The best way to understand Foundry is to see it run. Our flagship `production_run` example simulates a complete, interactive workflow for two different AI use cases.

#### Prerequisites
*   Python 3.8+
*   `git` and `pip`

#### Instructions
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/foundry.git
    cd foundry
    ```

2.  **Navigate to the example and install dependencies:**
    ```bash
    cd examples/production_run
    pip install -r requirements.txt
    ```

3.  **Run the interactive simulator:**
    ```bash
    python production_run.py
    ```

4.  **Follow the prompts:**
    *   The script will first ask you to **choose a use case** (Invoice OCR or Pole Detection).
    *   It will then ask you to **set a confidence threshold** for when the AI should ask for help.
    *   Finally, it will start a web server and give you a URL.

5.  **Open the URL in your browser (`http://localhost:8000`) and become the human in the loop.** Correct the AI's mistakes. When you're done, view the final report and export your work as a fine-tuning dataset.

---

## Core Concepts

Foundry's architecture is built on a few simple, powerful abstractions:

| Component | Description |
| :--- | :--- |
| **`Job`** | The central data model. Represents a single, discrete unit of work for the AI to perform and a human to potentially correct. |
| **`Pipeline`** | An orchestrator that runs a sequence of `Phase` objects, ensuring resilience by saving state after each step. |
| **`Phase`** | An abstract class representing a single, synchronous step in a `Pipeline` (e.g., call an OCR model, classify text). |
| **`AmbiguityDetector`** | A special class containing your business logic to find problems in an AI's output that require human clarification. |
| **`HumanInTheLoopPhase`** | A special `Phase` that runs your `AmbiguityDetector` and pauses the `Pipeline` if ambiguities are found. |
| **`CorrectionHandler`** | A service that handles saving human corrections and exporting them into a clean, model-ready dataset. |

## Project Philosophy

*   **It's the Glue, Not the Universe:** Foundry is not a monolithic MLOps platform or a complex labeling tool like Label Studio. It is the flexible, unopinionated "glue" that connects your application logic, your AI models, and your human operators into a single, resilient system.
*   **Developer Experience First:** The goal is to provide clean, Pythonic abstractions that are easy to understand, extend, and integrate into existing applications (e.g., FastAPI, Flask, Celery).
*   **UI-Agnostic:** The backend provides the hooks and data. You bring your own correction UI, whether it's a simple Jinja2 template, an interactive canvas, or a React frontend.

## Installation for Your Own Project

To use Foundry as a framework in your own application, you can install it directly from GitHub. It is recommended to install from a specific release tag to ensure stability.

```bash
# Install a specific version
pip install git+https://github.com/your-username/foundry.git@v0.1.0

# Or, install the latest version from the main branch (for development)
pip install git+https://github.com/your-username/foundry.git
```

## Contributing

We welcome contributions! This project is in its early stages, and we are actively looking for feedback and collaborators. Please feel free to open an issue to report a bug, suggest a feature, or ask a question.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
