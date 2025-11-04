# FILE: Dockerfile

# --- Base Image ---
# Start from an official NVIDIA image that includes CUDA 12.1 and cuDNN 8.
# This is the "foundation" that ensures our GPU libraries are correct.
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

# --- Environment Setup ---
# Set environment variables to prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# --- System Dependencies ---
# Install Python 3.10, pip, and other necessary system tools.
RUN apt-get update && \
    apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# --- Python Dependencies ---
# Copy the requirements file first to leverage Docker's layer caching.
# This step will only be re-run if requirements.txt changes.
COPY requirements.txt .

# Install the Python packages using pip
RUN pip3 install --no-cache-dir -r requirements.txt

# --- Application Code ---
# Copy the rest of the application code into the container
COPY . .

# --- Port and Command ---
# Expose the port the FastAPI server will run on
EXPOSE 8000

# The command to run when the container starts.
# We use --host 0.0.0.0 to make it accessible from outside the container.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
