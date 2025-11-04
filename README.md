
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

**Roadmap: Evolving Foundry from a Reactive Flywheel to an Autonomous Learning Loop**



### **Phase 1: Intelligent Data Curation (The "Smarter Filter")**

**Goal:** Move from passively correcting low-confidence samples to proactively identifying the most valuable data for a human to review.

*   **[ ] Task 1.1: Refactor the HITL Trigger to be Pluggable**
    *   Modify `HumanInTheLoopPhase` to accept a *list* of "Detector" objects instead of a single class.
    *   Create a base `Detector` abstract class that all detectors will inherit from. It should have a `detect(job)` method.
    *   Ensure the pipeline pauses if *any* detector in the list returns a `ClarificationRequest`.

*   **[ ] Task 1.2: Implement a Library of Basic Detectors**
    *   Create `foundry/detectors.py`.
    *   Migrate our existing logic into `LowConfidenceDetector(Detector)`.
    *   Create `RegexMismatchDetector(Detector)` that takes a field name and a regex pattern and flags jobs that don't match.
    *   Create `HeuristicDetector(Detector)` that takes a user-defined function (`lambda job: ...`) and flags a job if the function returns `True`.

*   **[ ] Task 1.3: Implement a Batch-Level "Active Learning" Detector**
    *   This is the core of this phase. Create a new `ActiveLearningPhase` that runs *after* a full batch of jobs has been processed by an initial AI phase.
    *   Create an `UncertaintySamplingDetector` that:
        1.  Gathers all prediction confidence scores from the batch.
        2.  Selects the top 'k' items with the lowest confidence (most uncertain).
        3.  Creates `ClarificationRequest`s only for these 'k' items.
    *   Create an `EmbeddingClusteringDetector` (Advanced):
        1.  Requires a `Phase` that generates embeddings for each job's output.
        2.  It clusters these embeddings (e.g., using `sklearn.cluster.KMeans`).
        3.  It selects a diverse set of samples by picking one from each cluster, prioritizing those closest to the cluster edge (most ambiguous).

*   **[ ] Task 1.4: Update the Example App**
    *   Modify the `local_finetuning_station` to include a new UI element allowing the user to choose their curation strategy: "Correct all below threshold" vs. "Correct the 10 most uncertain samples."


### **Phase 2: Amplifying Human Effort (The "Leverage Engine")**

**Goal:** Make every single human correction exponentially more valuable by using it to seed a synthetic data generation process.

*   **[ ] Task 2.1: Design the `SyntheticDataPhase`**
    *   Create a new `Phase` subclass called `SyntheticDataPhase`.
    *   This phase will be triggered *after* a `CorrectionRecord` is created.
    *   It will take the `CorrectionRecord` (containing the image and the human's correct label) as input.

*   **[ ] Task 2.2: Implement a Text-to-Text Synthesizer**
    *   Create a `TextAugmentationWorker` that can be called by the `SyntheticDataPhase`.
    *   Given a corrected text string, it uses a powerful LLM (e.g., Gemma) with specific prompts to generate realistic variations (rephrasing, changing tone, adding typos that are different from the original model's mistake).
    *   These synthetic text variations are saved as new, "synthetic" `CorrectionRecord`s.

*   **[ ] Task 2.3: Implement an Image-to-Image Synthesizer (Advanced)**
    *   Create an `ImageAugmentationWorker`.
    *   Given a corrected image and bounding box, it uses a generative model like **Stable Diffusion with ControlNet or LoRA**.
    *   It will generate variations of the image by changing backgrounds, lighting conditions, and camera angles while keeping the core object and its bounding box consistent.
    *   This is a complex task that requires significant research into generative model control.

*   **[ ] Task 2.4: Update the Training Worker**
    *   Modify the `training_worker` to be able to distinguish between "golden" human-provided records and "silver" synthetic records.
    *   It might use the synthetic data for standard fine-tuning and reserve the human data for the more powerful contrastive learning loop.


### **Phase 3: The Autonomous Supervisor (The "MLOps Brain")**

**Goal:** Automate the orchestration of the flywheel, elevating the human's role from worker to supervisor.

*   **[ ] Task 3.1: Create the Supervisor Service**
    *   This will be a separate, long-running process or a cron job.
    *   It will periodically query the database.

*   **[ ] Task 3.2: Implement Automated Training Triggers**
    *   The Supervisor will have a simple rule: `IF count(new_correction_records) > threshold (e.g., 100) AND last_training_run > 1 week ago THEN trigger_training_job()`.
    *   This will automatically call our `training_worker.py` script.

*   **[ ] Task 3.3: Implement Shadow Deployment & A/B Testing**
    *   Create a new table in `foundry/models.py` called `ModelAdapter` to track trained LoRA adapters and their versions.
    *   Modify the `inference_worker` to be able to load a specific adapter.
    *   The Supervisor will deploy the newly trained adapter in "shadow mode." It will route a small percentage (e.g., 5%) of live inference traffic to it.
    *   It will log the confidence scores and failure rates (number of items needing correction) for both the production model and the shadow model.

*   **[ ] Task 3.4: Implement Automated Promotion**
    *   The Supervisor will analyze the performance logs.
    *   If the shadow model consistently outperforms the production model over a set period (e.g., 24 hours), the Supervisor will automatically "promote" it, making it the new default model for all inference traffic.
    *   It should also have a mechanism to automatically roll back if the new model performs worse.

### **Phase 4: Real-Time Continual Learning (The "Live Teaching" Research)**

**Goal:** Explore and implement cutting-edge techniques for near-instantaneous model updates. This is a research-focused phase.

*   **[ ] Task 4.1: Research Model Editing Techniques**
    *   Investigate the current state-of-the-art in model editing, specifically for vision and vision-language tasks (e.g., ROME, MEMIT).
    *   Assess their stability, computational cost, and risk of catastrophic forgetting.

*   **[ ] Task 4.2: Create a `ModelEditingPhase` Prototype**
    *   Implement a new, experimental `Phase` that is triggered immediately after a correction.
    *   This phase would keep a base model "hot" in VRAM.
    *   It would apply the chosen model editing algorithm to make a surgical update to the model's weights based on the single correction.

*   **[ ] Task 4.3: Develop a "Live Teaching" UI**
    *   Create a new example UI that allows a user to interact with the model in real-time.
    *   **Workflow:** User provides an image -> Model makes a mistake -> User corrects the mistake -> The `ModelEditingPhase` runs -> User immediately provides a *similar* image to test if the model has learned from the correction.

*   **[ ] Task 4.4: Evaluate and Document**
    *   Rigorously evaluate the performance and stability of the live-editing model.
    *   Document the trade-offs between this approach and the more stable, batch-oriented fine-tuning method.

## Contributing

We welcome contributions! This project is in its early stages, and we are actively looking for feedback and collaborators. Please feel free to open an issue to report a bug, suggest a feature, or ask a question.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## White Paper: The Local Data Flywheel

### A Practical Architecture for Continual Learning on Consumer-Grade GPUs

**Date:** November 4, 2025  
**Authors:** knightbat2040

**Abstract:** The proliferation of powerful, open-source foundation models has shifted the primary challenge in applied AI from model creation to model specialization. The key to competitive advantage lies in creating a virtuous cycle where operational data is used to continuously fine-tune a generalist model into a domain-specific expert. Historically, this has required significant cloud compute resources and complex MLOps infrastructure. This paper outlines a novel, pragmatic architecture that makes this flywheel achievable on a single, consumer-grade GPU (e.g., with 8GB of VRAM), and proposes a Time-Slicing scheduling model for its future evolution into a truly autonomous learning system.

### **1. The Paradigm Shift: From Static Training to the Dynamic Data Flywheel**

The traditional machine learning lifecycle was a linear, high-latency process: collect a massive static dataset, spend months on labeling, train a model from scratch, and deploy it. This model would remain unchanged for long periods, slowly degrading as real-world data drifted.

The advent of parameter-efficient fine-tuning (PEFT) techniques like LoRA and quantization (QLoRA) has inverted this paradigm. It is now more efficient to start with a powerful pre-trained foundation model and iteratively specialize it with small, high-quality batches of correction data.

This creates the need for a **Data Flywheel**: an operational system designed to:
1.  **Execute** AI tasks in a production environment.
2.  **Triage** predictions where the model is uncertain.
3.  **Correct** these predictions via a human-in-the-loop (HITL).
4.  **Fine-Tune** the base model with these corrections to improve future performance.

The primary barrier to democratizing this powerful loop has been the perceived need for extensive, server-grade GPU resources. We argue that this is no longer the case.

### **2. The Core Challenge: Resource Contention on a Single GPU**

The data flywheel requires at least two distinct, computationally expensive modes of operation: **Inference** (using the model) and **Training** (improving the model). On a single GPU with a constrained VRAM budget (e.g., 8GB), these two modes are mutually exclusive. A model being fine-tuned can consume 2-3x its base memory footprint for gradients and optimizer states, making it impossible to concurrently run another model for inference.

Any viable single-GPU architecture must therefore be built around the principle of **serialized, modal execution**. The GPU must be treated as a singleton, mutex-protected resource.

### **3. The Foundry Architecture: A Modal, Worker-Based Solution**

We have implemented a solution to this problem in our Local Fine-Tuning Station, an open-source example built on the Foundry framework. The architecture is composed of three key components:

**A. The State Machine:** The application operates in a series of discrete, mutually exclusive states (`IDLE`, `INFERENCE`, `CORRECTION`, `TRAINING`, `COMPLETE`). This ensures the system has a clear understanding of its current task and resource requirements.

**B. The GPU Lock:** A simple, file-based mutex (`GPULock`) guarantees that only one process can access the GPU at any given time. Any process attempting to use the GPU while it is locked will simply wait, preventing catastrophic VRAM overflow errors.

**C. Decoupled, Background Workers:** The user-facing web server is decoupled from all heavy computation. GPU-intensive tasks are offloaded to separate, background processes:
*   An **Inference Worker** acquires the GPU lock, loads an inference-optimized model, processes the entire batch of user data, creates correction tasks, and then *explicitly unloads the model from VRAM* before releasing the lock.
*   A **Training Worker** acquires the GPU lock, loads a quantized base model, applies a PEFT/LoRA configuration, runs the fine-tuning loop on the corrected data, saves the resulting model adapter, and then *explicitly unloads the model* before releasing the lock.

This "coarse-grained" scheduling model is highly robust. It allows a single GPU to successfully power the entire data flywheel by ensuring that the distinct operational modes of Inference and Training never overlap in their resource claims. The user experience is modal: they are either in a correction phase (no GPU usage) or a training phase (100% GPU usage).

### **4. The Future: Fine-Grained "Time-Slicing" for a Seamless Experience**

While robust, the coarse-grained model forces the user into long, uninterruptible "Training Mode" sessions. The future evolution of this architecture lies in a more sophisticated, fine-grained scheduling model we call **Time-Slicing**.

The goal of Time-Slicing is to create the *illusion* of concurrency on a single GPU, enabling a more dynamic and interactive user experience. This is particularly relevant for the "Autonomous Learning Loop" paradigm, which requires a third, **Reasoning Worker** to analyze failures.

**The Time-Slicing Scheduler would operate as follows:**

1.  **Voluntary Lock Release:** The `Training Worker` would be modified. Instead of running for hours, it would train for a small, fixed number of steps (e.g., 10-20 seconds of work) and then voluntarily release the GPU lock. It would save its complete state (model weights, optimizer state, scheduler state) to disk or RAM.
2.  **Opportunistic Execution:** A master "Scheduler" process would see the GPU lock is free and could then launch another, short-lived worker. For example, it could launch the `Inference Worker` to process a few new incoming items or launch a `Reasoning Worker` to analyze recent failures.
3.  **Stateful Resumption:** Once the short-lived worker completes and releases the lock, the Scheduler would re-launch the `Training Worker`, which would seamlessly resume from its saved state.

This approach would interweave Training, Inference, and Reasoning tasks, giving the user near-real-time access to the system's capabilities without ever violating the single-process constraint of the GPU.

**Current Hurdles for Time-Slicing:**
*   **Model Loading Overhead:** The primary bottleneck is the significant time it takes to load and unload models from VRAM. Swapping models every 10-20 seconds would currently be inefficient, as much of the time would be spent on loading rather than computation.
*   **Framework Support:** Mainstream training frameworks are not yet optimized for this kind of rapid "pause and resume" workflow.

### **5. Conclusion**

It is entirely possible today to build a complete, end-to-end data flywheel for continual learning on a single, consumer-grade GPU. The key is a **modal, serialized architecture** that treats the GPU as a lockable resource, cleanly separating the Inference and Training workloads.

The future of this architecture lies in a **Time-Slicing scheduler**. As model loading becomes faster and training frameworks become more flexible, this approach will enable the development of truly autonomous, self-improving AI systems that can run effectively even on constrained, local hardware. This represents a significant step toward the democratization of production-grade AI, moving it from the exclusive domain of large cloud infrastructure into the hands of individual developers and researchers.

https://docs.run.ai/v2.17/Researcher/scheduling/GPU-time-slicing-scheduler/
