Foundry: Build Production-Grade AI Systems

![alt text](https://img.shields.io/badge/License-MIT-yellow.svg)


![alt text](https://img.shields.io/badge/python-3.8+-blue.svg)

<!-- Add other badges as we set them up, e.g., for build status, PyPI version, etc. -->


Foundry is a production-grade Python framework for building resilient, human-in-the-loop, fine-tuning data flywheels for generative AI.

It provides the architectural components you need when your AI project moves from a Jupyter Notebook to a real, continuously improving product.

The Problem

Building a simple AI prototype is easy. Building a robust, production-ready AI system that learns and improves is incredibly hard. Real-world AI systems face constant challenges:

Imperfect Models: Generative AI models are powerful but never 100% accurate. Their outputs require validation and correction.

Fragile Pipelines: Real-world AI tasks are multi-step processes. A failure in one step shouldn't bring down the entire system or lose valuable work.

Data Ambiguity: Sometimes, the AI lacks the context to make a confident decision. Forcing it to guess leads to low-quality results.

Stagnant Models: An AI model that doesn't learn from its mistakes will never improve, leading to a frustrating user experience and high operational costs.

The Solution: The Foundry Flywheel

Foundry provides the architectural components to solve these problems by helping you build a data flywheel: a virtuous cycle where your application's daily operations are turned into a scalable, ever-improving data generation engine.


Run Resilient Pipelines: Structure your AI tasks as a series of resilient Phases. If a step fails, the pipeline pauses, preserving the work from successful prior steps.

Ask for Help: When the system detects ambiguity, it automatically generates a ClarificationRequest, pausing the pipeline to ask a human for the specific information it needs through a simple UI.

Correct & Fine-Tune: All AI outputs can be reviewed by a human in a "Correction Deck" UI. Every correction is saved as a high-quality CorrectionRecord, creating a perfect dataset for fine-tuning your next-generation model.

Core Features

✅ Resilient, Multi-Step Pipelines: Define complex workflows as a sequence of simple, stateful Phases that automatically save their progress.

✅ Human-in-the-Loop Orchestration: Pause pipelines automatically with custom AmbiguityDetectors and generate a UI feed of questions for human operators.

✅ Automated Fine-Tuning Data Generation: Every human correction is automatically structured into a perfect .jsonl training example for fine-tuning.

✅ Asynchronous by Design: Built with Celery integration at its core, enabling scalable background processing for your AI tasks.

✅ Developer-Friendly Abstractions: Clean, abstract base classes (Pipeline, Phase, AmbiguityDetector) make it easy to plug in your own business logic.

Core Concepts

<!-- Re-using the flywheel diagram as it's the core architecture -->

Job: A single unit of work for the system, like processing one invoice or summarizing one document.

Pipeline: An orchestrator that runs a sequence of Phases to complete a Job.

Phase: A single, synchronous step in a Pipeline. Its state is saved upon successful completion, ensuring resilience.

CorrectionRecord: A self-contained, export-ready record containing the input, the model's flawed output, and the human's "ground truth" correction. This is the output of the flywheel.

AmbiguityDetector: A user-defined class that contains the logic for finding problems in a Job's output that require human clarification.

Installation
Prerequisites

Python 3.8+

pip and git

Installing the Package

You can install Foundry directly from this GitHub repository.

For Production Use:
It is recommended to install from a specific release tag to ensure stability.

pip install git+https://github.com/your-username/foundry.git@v0.1.0

For Development (Editable Mode):
Clone the repository and install it in editable mode to work on the framework itself.


# 1. Clone the repository
git clone https://github.com/your-username/foundry.git
cd foundry

# 2. Install in editable mode
pip install -e .
🚀 5-Minute Quickstart: The Data Flywheel in Action

This is the fastest way to see the core value of Foundry. It runs a local web server to demonstrate the "Correction Deck" UI, allowing you to fix an AI's mistakes and generate a fine-tuning data record.

No Celery or Redis required for this example.

Navigate to the example directory:

cd examples/correction_deck_quickstart

Run the quickstart script:

python quickstart.py
```    Your terminal will show a message that the server is running at `http://localhost:8000`.

Use the Correction Deck:

Open http://localhost:8000 in your browser.

You will see an invoice image and a form with flawed data extracted by an AI.

Fix the two errors: Correct the typo in the "Supplier Name" and change the quantity for "ONIONS YELLOW JBO" from 5 to 50.

Click "Save Correction".

Complete the Flywheel:

Go back to your terminal and stop the server by pressing Ctrl+C.

The script will automatically perform the final step: exporting your correction into a fine-tuning dataset.

Verify the Result:

A new file, corrected_data.jsonl, will now be in the directory.

Open it to see the perfectly structured, high-quality training example you just created. This file is ready to be used to fine-tune a better AI model.

What's Next? (Roadmap)

Foundry is an actively developing project. Our future goals include:

Pipeline Resumption Service: A built-in mechanism to automatically resume Jobs that have been un-paused by human feedback.

Command-Line Interface (CLI): Administrative tools for inspecting job statuses, re-running failed pipelines, and managing data exports.

More Pre-built Integrations: Simplified connectors for services like Hugging Face, Vertex AI, and OpenAI's fine-tuning APIs.

Enhanced UI Components: More pre-built, themeable Jinja2/HTMX templates for common Human-in-the-Loop tasks.

How to Contribute

We welcome contributions of all kinds! Whether it's reporting a bug, improving documentation, or submitting a pull request, your help is valued.

Please read our CONTRIBUTING.md file (we will create this) for details on our code of conduct and the process for submitting pull requests.

License

This project is licensed under the MIT License - see the LICENSE file for details.
