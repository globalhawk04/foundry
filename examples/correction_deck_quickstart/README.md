
### How to Use This `README.md`

1.  Create a new file named `README.md` inside the `examples/correction_deck_quickstart/` directory.
2.  Copy and paste the entire content below into that new file.
3.  Commit it to our repository.

---


# Foundry Quickstart: The Correction Deck & Data Flywheel

This quickstart is the fastest way to understand the core concept of the Foundry framework: **The Data Flywheel**.

It demonstrates how to build a simple, web-based "Correction Deck" that allows a human to fix the mistakes of an AI. Every correction is then automatically saved into a perfect, clean dataset that can be used to fine-tune a better AI model.

This example runs a simple, self-contained web server and **does not require Celery or Redis**.

## What You Will See

You will launch a web page that shows an invoice image on the left and a form on the right. The form is pre-filled with the flawed data extracted by an initial AI model. Your job is to fix the errors and save the correction.

![Correction Deck Screenshot](screenshot.png)
*(Note: We will need to take a screenshot of the working UI and save it as `screenshot.png` in this directory.)*

## How to Run This Example

These instructions assume you have already set up your virtual environment and installed the project dependencies from the root directory of this repository.

### Step 1: Navigate to the Example Directory

From the project's root `foundry/` directory, run:
```bash
cd examples/correction_deck_quickstart
```

### Step 2: Run the Quickstart Script

Make sure your virtual environment is activated, then start the web server:
```bash
python quickstart.py
```

You will see output in your terminal indicating the server has started:
```--- Foundry Quickstart Server running at http://localhost:8000 ---
--- Open the URL in your browser to use the Correction Deck. ---
--- Press Ctrl+C to stop the server and complete the flywheel. ---
```

### Step 3: Use the Correction Deck

Open your web browser and go to `http://localhost:8000`.

You will see the invoice correction UI. The initial AI made two mistakes. Your task is to fix them:
1.  **Fix the Typo:** In the "Supplier Name" field, change "Lone Star Provisins Inc." to **"Lone Star Provisions Inc."**
2.  **Fix the Quantity:** In the "ONIONS YELLOW JBO" row, change the quantity from `5` to **`50`**.

Once you have made the corrections, click the **"Save Correction"** button. Your browser will show a success page.

### Step 4: Complete the Flywheel

Go back to your terminal and stop the web server by pressing **`Ctrl+C`**.

When the server stops, the script automatically performs the final step: exporting your correction into a fine-tuning dataset. You will see this output:

```
--- Server stopped. ---

--- Exporting approved corrections to fine-tuning format... ---
--- Data successfully exported to 'corrected_data.jsonl' ---

--- QUICKSTART COMPLETE ---
```

### Step 5: Verify the Result

You have now completed one full turn of the data flywheel!

In the `correction_deck_quickstart` directory, you will find a new file named **`corrected_data.jsonl`**. Open it. This file contains a single line of perfectly structured JSONL, representing a high-quality training example that was created from your work.

This file is now ready to be used to fine-tune a more accurate AI model.
```