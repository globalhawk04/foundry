# Foundry Example: The Interactive Production Simulator

This is the flagship example for the Foundry framework. It moves beyond simple quickstarts to demonstrate a complete, interactive, and versatile production-grade workflow.

This self-contained application simulates a real-world batch processing job for two distinct AI use cases: **Invoice OCR** and **Utility Pole Detection**. It is the best way to understand the full, end-to-end power of the Foundry data flywheel: from initial AI prediction, to configurable human-in-the-loop triggers, to complex UI-based correction, and finally to the generation of a clean fine-tuning dataset.

## What You Will Experience

When you run this example, you will be guided through a complete simulation:

1.  **Choose Your Use Case:** You will select whether to process a batch of invoices (a structured data extraction task) or a batch of landscape photos (a computer vision task).
2.  **Set the AI's Confidence:** You will define the confidence threshold (e.g., 95% or `0.95`) that the system will use to decide when to ask for human help.
3.  **Correct the AI's Mistakes:** A web server will launch, presenting you with a "Clarification Feed." You will be asked to review only the jobs that fell below your confidence threshold.
    *   For **Invoices**, you will see a web form with highlighted fields containing typos or incorrect values.
    *   For **Pole Detection**, you will use an interactive canvas editor to delete incorrectly drawn bounding boxes and draw new ones for missed objects.
4.  **See the Results & Export:** After you've cleared the review queue, you will see a final report page summarizing the entire batch. It will visually distinguish between the jobs the AI handled automatically and the ones you personally corrected. From here, you can export your corrections into a perfect `.jsonl` file, ready for the next fine-tuning run.

## Core Concepts Demonstrated

*   **Domain Flexibility:** Shows how the same Foundry models (`Job`, `CorrectionRecord`) and pipeline concepts can handle vastly different AI problems (text vs. vision).
*   **Configurable HITL Triggers:** Demonstrates a practical `AmbiguityDetector` that uses a configurable confidence score to pause the pipeline, moving beyond simple rule-based triggers.
*   **Complex Correction UIs:** Proves that Foundry is UI-agnostic by supporting both a standard HTML form and a sophisticated JavaScript-based canvas editor.
*   **The Complete Data Flywheel:** You will participate in one full, tangible turn of the flywheel—from flawed AI output to a clean, export-ready dataset generated from your corrections.

## How to Run This Example

### Prerequisites

You will need the dependencies for this example. Create a file named `requirements.txt` in this directory (`examples/production_run/`) and paste the following content into it:

```txt
# FILE: requirements.txt
fastapi
uvicorn[standard]
SQLAlchemy
Jinja2
questionary
```

Now, from your terminal, install these dependencies:

```bash
pip install -r requirements.txt
```

### Step 1: Navigate to the Example Directory

From the project's root `foundry/` directory, run:
```bash
cd examples/production_run
```

### Step 2: Run the Simulation Script

Make sure your virtual environment is activated, then start the main script:
```bash
python production_run.py
```

### Step 3: Interact with the Command-Line Prompts

The script will ask you two questions in your terminal:
1.  **Which production run would you like to simulate?**
    *   Use the arrow keys to choose either `Invoice Processing` or `Utility Pole Detection` and press Enter.
2.  **Enter the confidence threshold for human review (e.g., 0.95):**
    *   You can accept the default by pressing Enter, or type a different value (e.g., `0.80`) to see how it changes the number of items you have to review.

The script will then simulate the initial AI batch run and start the web server.

### Step 4: Use the Web UI for Correction

Once the server is running, open your web browser and go to `http://localhost:8000`.

You will be presented with the first job that requires your review.
*   If you chose **Invoices**, correct the highlighted fields and click "Save Correction & Load Next".
*   If you chose **Pole Detection**, use your mouse to delete bad boxes and draw new ones, then click "Save Correction & Load Next".

Continue this process until you see the "All Done!" message.

### Step 5: View the Report and Export

Click the "View Final Report" button. You will be taken to a summary page showing all the jobs from the batch. The jobs you personally fixed will have a green border and a "✅ Corrected by You" badge.

To complete the flywheel, click the **"Export for Fine-Tuning"** button to download the `corrected_data.jsonl` file containing your high-quality training data. You can now stop the server in your terminal by pressing `Ctrl+C`.
