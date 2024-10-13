

import os
import torch
from datasets import Dataset, DatasetDict, load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments, pipeline
from peft import LoraConfig, PeftModel, prepare_model_for_kbit_training
from trl import SFTTrainer
import pandas as pd

# 1. EDA and Preprocessing

# Define your labeled email dataset
data = {
    "instruction": [
        "Please respond to the following email inquiry:",
        "Please provide assistance regarding the following customer inquiry:",
        "Respond to the customer's inquiry with relevant information:",
        "Reply to the following email with details about our subscription plans:",
        "Please address the login issue reported in the following email:"
    ],
    "output": [
        "Sure, here's an overview of our products and services...",
        "Of course, I'd be happy to assist you with your account issues...",
        "Certainly, let me check on the status of your order and get back to you...",
        "Certainly, here are the subscription plans we offer along with their benefits...",
        "I apologize for the inconvenience. Let's troubleshoot the login issue together..."
    ],
    "category": ["request", "request", "question", "request", "question"],
    "preferred_reaction": ["respond", "respond", "respond", "respond", "respond"]
}

# Convert data into a DataFrame and Hugging Face Dataset format
df = pd.DataFrame(data)
hf_dataset = Dataset.from_pandas(df)
dataset_dict = DatasetDict({"train": hf_dataset})

# Define a function to apply template to dataset
def format_example(example):
    example["instruction"] = (
        f"### Instruction:\n{example['instruction']}\n"
        f"Category: {example['category']}\n"
        f"Preferred Reaction: {example['preferred_reaction']}\n\n### Response:\n"
    )
    return example

# Apply formatting template
dataset_dict = dataset_dict.map(format_example)

# 2. Model Setup (LLaMA 3B)

# Load LLaMA 3B model and tokenizer
base_model = "meta-llama/Llama-3B"
tokenizer = AutoTokenizer.from_pretrained(base_model, use_fast=True)
tokenizer.pad_token = tokenizer.unk_token
tokenizer.padding_side = "right"

# Quantization configuration for efficient training
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

# LoRA configuration for fine-tuning
peft_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
    target_modules=['up_proj', 'down_proj', 'gate_proj', 'k_proj', 'q_proj', 'v_proj', 'o_proj']
)

# Load base model
model = AutoModelForCausalLM.from_pretrained(
    base_model,
    quantization_config=bnb_config,
    device_map={"": 0}
)

# Prepare model for 4-bit training
model = prepare_model_for_kbit_training(model)

# 3. Fine-tuning on labeled data

# Set training arguments
training_arguments = TrainingArguments(
    output_dir="./results",
    num_train_epochs=1,
    per_device_train_batch_size=10,
    gradient_accumulation_steps=1,
    evaluation_strategy="steps",
    eval_steps=1000,
    logging_steps=1,
    optim="paged_adamw_8bit",
    learning_rate=2e-4,
    lr_scheduler_type="linear",
    warmup_steps=10,
    report_to="wandb",
    max_steps=2,
)

# Initialize trainer for fine-tuning
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset_dict["train"],
    eval_dataset=dataset_dict["train"],
    peft_config=peft_config,
    dataset_text_field="instruction",
    max_seq_length=512,
    tokenizer=tokenizer,
    args=training_arguments,
)

# Start fine-tuning
trainer.train()

# Save the fine-tuned model
fine_tuned_model = "llama-3b-finetuned"
trainer.model.save_pretrained(fine_tuned_model)

# 4. Testing and Validation

# Inference: Generate responses based on a new prompt
pipe = pipeline(task="text-generation", model=model, tokenizer=tokenizer, max_length=512)

# Define test input text
input_text = "Can you provide me with information about your subscription plans?"
prompt = f"""### Instruction:
Given the input provided below, respond to it in the format of an email.

Input:
{input_text}

Response:
"""

# Generate the response
result = pipe(f"[INST] {prompt} [/INST]")
generated_response = result[0]['generated_text'][len(prompt):]

# Print the generated response
print(generated_response)
