Foundry Quickstart: The Human-in-the-Loop Pipeline

This quickstart demonstrates one of the most powerful features of the Foundry framework: a resilient, interactive, Human-in-the-Loop (HITL) pipeline.

Where the "Correction Deck" example shows how to fix a completed job's output (an offline flywheel), this example shows how a running pipeline can automatically pause itself, ask a human for help, and then wait to be resumed (an online flywheel).

This example runs a simple, self-contained web server and does not require Celery or Redis.

What You Will See

You will run a script that first simulates a stalled AI job. Then, it will launch a web UI called the "Clarification Feed." This feed presents a simple question to you, the human operator. Your answer will directly un-pause the stalled job.

![alt text](screenshot.png)

(Note: We will need to take a screenshot of the working UI and save it as screenshot.png in this directory.)

Core Concepts Demonstrated

AmbiguityDetector: A custom class (UnlinkedProductDetector) that contains the business logic to find problems in an AI's output.

HumanInTheLoopPhase: A special pipeline phase that runs a detector and pauses the pipeline if ambiguities are found.

Pipeline Pausing: See how a Job's status changes from in_progress to pending_clarification and finally to ready_for_final_processing.

Dynamic UI Rendering: The example uses Jinja2 and HTMX to create a simple but effective UI that requests the exact information the system needs.

How to Run This Example

These instructions assume you have already set up your virtual environment and installed the project dependencies from the root directory of this repository.

### Step 1: Navigate to the Example Directory

From the project's root foundry/ directory, run:```bash
cd examples/human_in_the_loop_example

### Step 2: Run the Quickstart Script

Make sure your virtual environment is activated, then start the script:
```bash
python hhuman_in_the_loop_example.py
Step 3: Observe the Initial Output

The script will first run a pipeline in your terminal to detect the ambiguity. You will see this output, which confirms the job has been paused:

code
Code
download
content_copy
expand_less
--- Setting up the database... ---
--- Job #1 created. ---

--- Running the Ambiguity Detection Pipeline for Job #1... ---
--- [Job 1] Running Phase: HumanInTheLoopPhase ---
--- [Job 1] Found 1 ambiguities. Pausing pipeline. ---
--- [Job 1] Phase 'HumanInTheLoopPhase' Succeeded. State saved. ---
--- Pipeline finished. Job status is now: 'pending_clarification' ---

Next, the web server will start:

code
Code
download
content_copy
expand_less
--- Human-in-the-Loop server running at http://localhost:8000 ---
--- Open the URL in your browser to answer the clarification question. ---
--- After resolving, press Ctrl+C to stop the server. ---
Step 4: Use the Clarification Feed

Open your web browser and go to http://localhost:8000.

You will see the UI asking you to link the "ONIONS YELLOW JBO" item to a product.

From the Select Product dropdown, choose "Yellow Onions".

Click the "Link Product" button.

The UI will update to show "All Done!", and in your terminal, you will see a log confirming the job's status has been changed:

code
Code
download
content_copy
expand_less
--- Received resolution for request #1 with data: {'pantry_item_id': ['102'], 'request_type': ['LINK_PRODUCT']} ---
--- Request #1 resolved. Job #1 is now 'ready_for_final_processing'. ---
Step 5: Stop the Server and Verify the Result

Go back to your terminal and stop the web server by pressing Ctrl+C.

The script will then print a final verification message showing the final state of the objects in the database:

code
Code
download
content_copy
expand_less
--- Server stopped. ---

--- Final Job Status: ready_for_final_processing ---
--- Final Request Status: resolved ---
--- User's Answer was: {'user_answer': {'pantry_item_id': ['102'], 'request_type': ['LINK_PRODUCT']}} ---

--- HUMAN-IN-THE-LOOP EXAMPLE COMPLETE ---

You have now successfully acted as the "human in the loop," providing the missing piece of information to a paused AI process. The job is now ready for a final pipeline to take over and complete the work.
