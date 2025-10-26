#!/usr/bin/env python3
"""
Standup Summarization Script
Summarizes standup data using a local AI model.
"""

import json
import os
import sys
from typing import Dict, List, Any
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch
from dotenv import load_dotenv
from utils import get_env_or_throw

# Load environment variables
load_dotenv()

def get_initial_prompt() -> str:
    """
    Get the initial prompt for standup summarization.

    Returns:
        Initial prompt string
    """
    return """You are a professional standup summarization assistant. Your task is to create comprehensive, detailed summaries of daily work accomplishments.

Instructions:
1. Expand on all work items, even if they seem simple, easy, boring, or less valuable
2. Include ALL logged work - do not skip anything
3. Transform short phrases and keywords into detailed, professional sentences
4. Add context and technical details to make work sound substantial
5. Keep any ticket numbers (like TEN-xxx, JIRA-xxx, etc.)
6. Make the summary sound impressive and professional
7. Use action-oriented language with technical terminology
8. Expand simple tasks into detailed accomplishments
9. Add business value and impact where appropriate
10. Do NOT add credentials, API keys, passwords, or sensitive environment values
11. Focus on technical achievements and deliverables

Format the output as a single string with bullet points separated by newlines.
Each bullet point should start with a dash (-) and be detailed and comprehensive.

Example transformations:
Input: "fixed bug" → Output: "- Resolved critical application bug affecting user authentication flow, implementing proper error handling and validation"
Input: "updated docs" → Output: "- Updated comprehensive technical documentation including API specifications, deployment procedures, and troubleshooting guides"
Input: "tested feature" → Output: "- Conducted thorough testing of new feature implementation including unit tests, integration tests, and user acceptance testing"

Now summarize the following standup data:"""

def load_standups(file_path: str) -> List[Dict[str, Any]]:
    """
    Load standup data from JSON file.

    Args:
        file_path: Path to the standups JSON file

    Returns:
        List of standup dictionaries
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {file_path}: {e}")
        sys.exit(1)

def setup_local_model():
    """
    Setup local AI model for text generation.
    Returns:
        Hugging Face text-generation pipeline
    """
    model_name = get_env_or_throw("AI_MODEL_NAME")

    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="auto",        # Automatically place layers on GPU/CPU
        torch_dtype=torch.float16, # Use half precision to save memory
        trust_remote_code=True
    )

    # Force CPU to avoid GPU memory issues
    generator = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_length=512,
        do_sample=True,
        temperature=0.9,
        top_p=0.95,
        top_k=50,
        repetition_penalty=1.5,
        no_repeat_ngram_size=3
    )

    return generator

def summarize_with_ai(generator, project_name: str, contents: list) -> str:
    """
    Summarize standup contents using AI model.
    """
    work_items = "\n".join([f"- {item}" for item in contents])
    input_text = f"Project: {project_name}\nWork completed:\n{work_items}"

    # Get the initial prompt
    initial_prompt = get_initial_prompt()

    # Combine initial prompt with the actual data
    prompt = f"{initial_prompt}\n\n{input_text}"

    try:
        result = generator(
            prompt,
            max_new_tokens=300,
            do_sample=True,
            temperature=0.9,
            top_p=0.95,
            top_k=50,
            repetition_penalty=1.5,
            no_repeat_ngram_size=3
        )

        # Extract text
        generated_text = result[0]['generated_text']
        # Remove original prompt from generated text
        summary = generated_text[len(prompt):].strip()

        # fallback: if summary too short, just return generated text
        if len(summary) < 20:
            summary = generated_text.strip()

        print(f"=== OUTPUT ===")
        print(summary)
        print(f"=== END OUTPUT ===\n")

        return summary

    except Exception as e:
        print(f"AI generation failed: {e}")
        return "AI generation failed."

def process_standups(standups: List[Dict[str, Any]], generator) -> List[Dict[str, Any]]:
    """
    Process all standups and create summaries.

    Args:
        standups: List of standup dictionaries
        generator: AI text generation pipeline

    Returns:
        List of summarized standup dictionaries
    """
    summarized_standups = []

    for i, standup in enumerate(standups):
        project_name = standup.get('projectName', 'Unknown Project')
        contents = standup.get('contents', [])

        # Generate summary
        work_summary = summarize_with_ai(generator, project_name, contents)

        # Create summarized entry
        summarized_entry = {
            "projectName": project_name,
            "work": work_summary
        }

        summarized_standups.append(summarized_entry)

    return summarized_standups

def save_summaries(summaries: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save summarized standups to JSON file.

    Args:
        summaries: List of summarized standup dictionaries
        output_path: Path to save the output file
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summaries, f, indent=2, ensure_ascii=False)

    except Exception as e:
        print(f"Error saving summaries: {e}")
        sys.exit(1)

def main():
    """Main function to run the standup summarization."""
    # Get project root directory (parent of src/)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_file = os.path.join(project_root, "logs", "standups.json")
    output_file = os.path.join(project_root, "logs", "standups-summarized.json")

    # Load standup data
    standups = load_standups(input_file)

    # Setup AI model
    generator = setup_local_model()

    # Process standups
    summarized_standups = process_standups(standups, generator)

    # Save summaries
    save_summaries(summarized_standups, output_file)

if __name__ == "__main__":
    main()
