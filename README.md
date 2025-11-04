
# Foundry: The Framework for Production-Grade AI Data Flywheels

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/your-username/foundry)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

**Go from a fragile AI prototype to a resilient, self-improving production system.**

Foundry is a Python framework for building the operational backbone of modern AI applications. It provides the architectural components to create resilient, human-in-the-loop data flywheels, turning the necessary work of correcting AI mistakes into a scalable engine for continuous model improvement.



## The Problem: Production AI is a Game of Exceptions

Getting an AI model to 85% accuracy is easier than ever. Getting it from 85% to a production-ready 99% is where most projects fail. The real world is messy, and production systems must be built to handle the inevitable exceptions:

*   **Imperfect Models:** Foundation models are generalists. They make mistakes on your specific, domain-critical data, leading to a poor user experience.
*   **Fragile Pipelines:** Real-world tasks are multi-step processes. A single failure in an OCR or extraction step shouldn't halt an entire batch or lose valuable work.
*   **Stagnant Models:** An AI that doesn't learn from its operational mistakes will never improve, leading to high manual correction costs and a frustrating user experience.

## The Solution: The Foundry Data Flywheel

Foundry provides the structure to build a **virtuous cycle** where every human intervention makes your AI system smarter, more accurate, and more autonomous.


### How It Works

1.  **Resilient Execution:** You structure your task as a `Pipeline` of resilient `Phases`. The system processes a batch of jobs, saving state after each step.
2.  **Automated Triage:** Your custom `AmbiguityDetector` (based on confidence scores or business logic) automatically flags jobs where the AI is uncertain. The `HumanInTheLoopPhase` pauses the pipeline for these specific jobs.
3.  **Human Correction:** A human operator reviews the flagged jobs in a UI. Foundry is UI-agnostic, supporting everything from simple web forms to complex canvas editors. Every fix is saved as a perfect `CorrectionRecord`.
4.  **Fine-Tuning & Redeployment:** The collected `CorrectionRecord`s are exported into a clean `.jsonl` dataset. You use this data to fine-tune your model (e.g., Gemma, Llama, TrOCR). The newly fine-tuned model replaces the old one, and the flywheel spins again, requiring less human intervention on the next cycle.

---

## See Foundry in Action

We offer two powerful examples to demonstrate the framework's capabilities.

### 🚀 Quick Demo: The Correction Flywheel

This example runs a simple, self-contained web server (no Docker or GPU required) that simulates an Invoice OCR workflow. It's the fastest way to understand the core data correction and export loop.

1.  **Clone the repository:** `git clone https://github.com/your-username/foundry.git && cd foundry`
2.  **Navigate to the example and install dependencies:**
    ```bash
    cd examples/production_run
    pip install -r requirements.txt
    ```
3.  **Run the interactive simulator:**
    ```bash
    python production_run.py
    ```
4.  **Follow the prompts, open `http://localhost:8000`**, and use the web UI to correct the AI's mistakes and export the final dataset.



### 🧠 Advanced Demo: The Local Fine-Tuning Station

This is the flagship example. It is a complete, containerized application that allows you to perform **"one-click" local fine-tuning of an OCR model on your own data** using a consumer NVIDIA GPU.

> **⚠️ Advanced Setup Required:** This demo requires **Docker**, an **NVIDIA GPU (>=8GB VRAM)**, and the **NVIDIA Container Toolkit**.

1.  **Navigate to the advanced example:**
    ```bash
    cd examples/local_finetuning_station
    ```
2.  **Build and run the containerized application:**
    ```bash
    # This will take several minutes on the first run
    docker-compose build
    docker-compose up
    ```
3.  **Open `http://localhost:8000`** and follow the workflow: upload your own images, correct the AI's transcriptions, and trigger the fine-tuning process directly from the UI, all on your local machine.

---

## Project Philosophy

*   **The Bridge, Not the Island:** Foundry is not a monolithic MLOps platform or a replacement for Label Studio. It is the **specialized bridge** that connects your application logic, your AI models, and your human operators. It fills the critical gap between workflow orchestration and data annotation.
*   **Developer Experience First:** The goal is to provide clean, Pythonic abstractions (`Pipeline`, `Phase`, `CorrectionRecord`) that are easy to understand and integrate into existing applications built with tools like FastAPI, Flask, and Celery.
*   **UI-Agnostic:** The backend provides the data and the state machine. You bring your own correction UI, whether it's a simple Jinja2 template, an interactive canvas, or a React frontend.

## Installation for Your Own Project

To use Foundry as a library in your own application, install it directly from GitHub.

```bash
# It is recommended to install from a specific release tag for stability
pip install git+https://github.com/your-username/foundry.git@v0.1.0

# Or, install the latest version for development
pip install git+https://github.com/your-username/foundry.git
```

## What's Next: A Pluggable Architecture

Our vision is to evolve Foundry into a fully pluggable framework. Future versions will include:
*   A library of swappable **`Detectors`** (for confidence, heuristics, active learning).
*   A library of swappable **`Exporters`** for different fine-tuning formats (OpenAI, Hugging Face TRL).
*   A basic **UI Kit** of pre-built Jinja2/HTMX components for common correction tasks.

## Contributing

We welcome contributions! This project is in its early stages, and we are actively looking for feedback and collaborators. Please feel free to open an issue to report a bug, suggest a feature, or ask a question.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
