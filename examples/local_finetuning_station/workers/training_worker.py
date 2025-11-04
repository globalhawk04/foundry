# FILE: workers/training_worker.py (Corrected and Finalized)

import os
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    TrOCRProcessor,
    VisionEncoderDecoderModel,
    AdamW,
    get_scheduler
)
from peft import LoraConfig, get_peft_model
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import traceback

# --- Application & Foundry Imports ---
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.state import AppState, AppStatus, AppMode
from app.gpu_lock import GPULock
from foundry.models import Base, CorrectionRecord

# ==============================================================================
# 1. CONFIGURATION & DATABASE SETUP
# ==============================================================================
DB_PATH = "data/foundry.db"
engine = create_engine(f"sqlite:///{DB_PATH}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Training Hyperparameters ---
NUM_TRAINING_EPOCHS = 10
LEARNING_RATE = 5e-5
LORA_R = 8
LORA_ALPHA = 16
BATCH_SIZE = 1 # Must be 1 on an 8GB GPU to fit in memory

# ==============================================================================
# 2. CUSTOM PYTORCH DATASET
# ==============================================================================

class ContrastiveOCRDataset(Dataset):
    """
    A custom PyTorch dataset that creates positive and negative pairs
    from Foundry CorrectionRecords.
    """
    def __init__(self, records, processor):
        self.records = records
        self.processor = processor

    def __len__(self):
        return len(self.records)

    def __getitem__(self, idx):
        record = self.records[idx]
        image_path = record.source_input["path"]
        image = Image.open(image_path).convert("RGB")
        pixel_values = self.processor(images=image, return_tensors="pt").pixel_values
        
        return {
            "pixel_values": pixel_values.squeeze(0),
            "positive_text": record.human_correction["text"],
            "negative_text": record.model_output["text"]
        }

# ==============================================================================
# 3. CUSTOM PYTORCH TRAINER CLASS
# ==============================================================================

class ContrastiveTrainer:
    """
    A custom trainer to handle the contrastive learning loop.
    """
    def __init__(self, model, optimizer, train_dataloader, device):
        self.model = model
        self.optimizer = optimizer
        self.train_dl = train_dataloader
        self.device = device
        self.num_epochs = NUM_TRAINING_EPOCHS
        self.loss_fn = torch.nn.MarginRankingLoss(margin=1.0)
        self.lr_scheduler = get_scheduler(
            name="linear", optimizer=self.optimizer,
            num_warmup_steps=0, num_training_steps=len(self.train_dl) * self.num_epochs
        )

    def _calculate_contrastive_loss(self, batch):
        pixel_values = batch["pixel_values"].to(self.device)
        positive_labels = batch["positive_labels"].to(self.device)
        negative_labels = batch["negative_labels"].to(self.device)

        # Positive pass: The loss for the correct transcription
        outputs_pos = self.model(pixel_values=pixel_values, labels=positive_labels)
        loss_pos = outputs_pos.loss

        # Negative pass: The loss for the incorrect transcription
        outputs_neg = self.model(pixel_values=pixel_values, labels=negative_labels)
        loss_neg = outputs_neg.loss
        
        target = torch.ones(loss_pos.size()).to(self.device)
        return self.loss_fn(loss_neg, loss_pos, target)

    def train(self):
        self.model.train()
        for epoch in range(self.num_epochs):
            total_loss = 0
            for i, batch in enumerate(self.train_dl):
                self.optimizer.zero_grad()
                loss = self._calculate_contrastive_loss(batch)
                loss.backward()
                self.optimizer.step()
                self.lr_scheduler.step()
                total_loss += loss.item()
                AppState.set_status(AppStatus.TRAINING, f"Epoch {epoch+1}/{self.num_epochs}, Step {i+1}/{len(self.train_dl)}, Loss: {loss.item():.4f}")
            
            avg_loss = total_loss / len(self.train_dl)
            print(f"Epoch {epoch+1} finished. Average Loss: {avg_loss:.4f}")

# ==============================================================================
# 4. MAIN WORKER FUNCTION
# ==============================================================================

def run_training(model_type: AppMode):
    """
    The main function for the training worker process.
    """
    db = SessionLocal()
    with GPULock(owner="TrainingWorker"):
        try:
            AppState.set_status(AppStatus.TRAINING, "Initializing training worker...")
            
            correction_records = db.query(CorrectionRecord).all()
            if not correction_records:
                raise ValueError("No corrections found to fine-tune on.")
            
            AppState.set_status(AppStatus.TRAINING, "Loading base model for fine-tuning...")
            device = "cuda" if torch.cuda.is_available() else "cpu"

            processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-handwritten')
            model = VisionEncoderDecoderModel.from_pretrained(
                'microsoft/trocr-base-handwritten', load_in_4bit=True, device_map="auto"
            )

            lora_config = LoraConfig(
                r=LORA_R, lora_alpha=LORA_ALPHA, lora_dropout=0.05,
                target_modules=["q_proj", "v_proj"], bias="none"
            )
            model = get_peft_model(model, lora_config)
            model.print_trainable_parameters()

            dataset = ContrastiveOCRDataset(correction_records, processor)
            
            def collate_fn(batch):
                pixel_values = torch.stack([item['pixel_values'] for item in batch])
                pos_texts = [item['positive_text'] for item in batch]
                neg_texts = [item['negative_text'] for item in batch]
                
                pos_labels = processor(text=pos_texts, padding=True, return_tensors="pt").input_ids
                neg_labels = processor(text=neg_texts, padding=True, return_tensors="pt").input_ids
                
                return {
                    'pixel_values': pixel_values,
                    'positive_labels': pos_labels,
                    'negative_labels': neg_labels
                }

            train_dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate_fn)

            optimizer = AdamW(model.parameters(), lr=LEARNING_RATE)
            trainer = ContrastiveTrainer(model, optimizer, train_dataloader, device)
            
            trainer.train()

            AppState.set_status(AppStatus.TRAINING, "Saving fine-tuned model adapter...")
            save_path = "models/final_lora_adapter"
            model.save_pretrained(save_path)
            print(f"LoRA adapter saved to {save_path}")

            del model
            del processor
            torch.cuda.empty_cache()
            
            AppState.set_status(AppStatus.COMPLETE, "Fine-tuning complete! The model is ready.")

        except Exception as e:
            print(f"FATAL ERROR in training worker: {e}")
            traceback.print_exc()
            AppState.set_status(AppStatus.ERROR, f"An error occurred during training: {e}")
        finally:
            db.close()
            print("Training worker finished and released resources.")