
# Foundry Advanced Example: The Local Fine-Tuning Station

Welcome to the flagship example for the Foundry framework. This is a powerful, self-contained application that demonstrates a complete, end-to-end **AI data flywheel in a box**.

This tool is designed for **advanced users** who want to fine-tune a powerful, open-source AI model for a specific visual task (like OCR) using their own data, all on a local machine with a consumer-grade NVIDIA GPU.

It moves beyond simple scripts to provide a complete, interactive workflow: from data upload, to AI-assisted correction, to "one-click" local fine-tuning, and finally to a ready-to-use, domain-specific model adapter.

---

## What This Application Does

The "Local Fine-Tuning Station" guides you through one full, tangible turn of the data flywheel:

1.  **Upload & Configure:** You start the application and are greeted with a web UI. You upload a `.zip` file of your images and set a confidence threshold that defines the AI's "uncertainty level."

2.  **Automated First Pass (Inference):** The system uses a pre-trained base model (`microsoft/trocr-base-handwritten` for OCR) to perform an initial analysis of every image.

3.  **Human-in-the-Loop Correction:** The application's UI then presents you with a "Clarification Feed." This feed only contains the images where the AI's confidence was below your set threshold. You correct the AI's mistakes in the UI.

4.  **"One-Click" Advanced Fine-Tuning:** Once all corrections are complete, you click a "Begin Fine-Tuning" button. The application automatically:
    *   Switches into a dedicated **"Training Mode"** to focus all GPU resources on the task.
    *   Initiates a **parameter-efficient fine-tuning (PEFT/QLoRA)** process on your local GPU.
    *   Uses a **custom contrastive training loop**, teaching the model not only what the *correct* answer is but also forcing it to learn that its *previous mistake* was wrong.

5.  **Result & Deployment:** After the training process completes, you are presented with the final result: a small, trained **LoRA adapter**. This adapter file can be easily loaded on top of the base model for highly accurate inference in your own applications.

---

## ⚠️ Prerequisites: This is an Advanced Setup

This example is powerful because it runs a complex AI training environment on your local machine. This requires a specific hardware and software setup. **Please ensure you meet these requirements before proceeding.**

1.  **Hardware:** An **NVIDIA GPU** with at least **8GB of VRAM**. This will not work on AMD or Apple Silicon GPUs.
2.  **NVIDIA Drivers:** You must have the latest NVIDIA drivers for your GPU installed on your host machine.
3.  **Docker:** You must have Docker and Docker Compose (or Docker Desktop) installed and running.
4.  **NVIDIA Container Toolkit:** You must install the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html). This is the critical piece that allows Docker containers to access your GPU. You can verify it's working by running `docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi`.

### Why Docker?

This example is not a simple Python script. It relies on a complex stack of NVIDIA drivers, the CUDA Toolkit, and compiled C++ libraries (`bitsandbytes`). A standard Python virtual environment cannot manage this complexity.

Docker is used to provide a **guaranteed, reproducible environment** where all these low-level dependencies are pre-configured correctly. This allows you to focus on the AI workflow, not on debugging system library conflicts.
---

## How to Run This Example

### Step 1: Build the Docker Image

Navigate to this directory (`examples/local_finetuning_station/`) in your terminal. Build the Docker image using the provided `docker-compose.yml` file. This will download the CUDA base image and install all the necessary Python dependencies in a perfectly configured environment.

This step will take a significant amount of time (10-30 minutes) on the first run as it downloads several gigabytes of data.

```bash
docker-compose build
```

### Step 2: Run the Application

Once the build is complete, start the application. The `docker-compose up` command will start the container and correctly mount the `data/` and `models/` directories, so your work will be saved on your local machine.

```bash
docker-compose up
```

You will see log output from the Uvicorn server. Once it says `Application startup complete`, the station is ready.

### Step 3: Use the Web UI

Open your web browser and navigate to `http://localhost:8000`.

1.  **Upload Your Data:** You will see the upload screen. Prepare a `.zip` file containing 10-100 images for your OCR task. Use the form to upload your zip file and set your desired confidence threshold. Click **"Start Inference."**
2.  **Wait for Inference:** The UI will show an "Inference in Progress" message. This may take a few minutes as the model is downloaded and run on your images.
3.  **Correct the Data:** Once inference is complete, the UI will automatically switch to the correction feed. Review each image and provide the correct text transcription. Click **"Save Correction & Load Next."**
4.  **Start Fine-Tuning:** After the last correction, you will be taken to the pre-training summary page. Click the **"Start Fine-Tuning Process"** button to begin.
5.  **Monitor Training:** The UI will now show the live progress of the training loop. You can watch the loss decrease as the model learns from your corrections.
6.  **Get Your Result:** When training is complete, the UI will show a success message and provide a code snippet showing you how to use your new model adapter.

### Step 4: Access Your Trained Model

The trained LoRA adapter will be saved to the `models/final_lora_adapter/` directory on your host machine, inside the `local_finetuning_station` folder. You can now use this adapter in any other project, as shown in the code snippet on the completion page.

### Step 5: Shut Down the Application

To stop the application, go to your terminal where `docker-compose up` is running and press `Ctrl+C`.
