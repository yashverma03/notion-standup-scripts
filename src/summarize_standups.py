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
    return """Transform these work items into professional bullet points. Expand each item into a detailed accomplishment:

Example:
Input: "fixed bug in rent flow"
Output: "- Resolved critical bug in rental payment processing system, ensuring smooth transaction flow and improved user experience"

Input: "small ui glitch gone"
Output: "- Fixed minor UI rendering issue that was causing visual inconsistencies, enhancing overall user interface quality"

Input: "retry job half done"
Output: "- Implemented robust retry mechanism for failed background jobs, improving system reliability and error handling"

Now transform these work items:"""

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
        Text generation pipeline
    """
    try:
        # Get model name from environment variable
        model_name = get_env_or_throw("AI_MODEL_NAME")
        print(f"Using AI model: {model_name}")

        print("Loading local AI model...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)

        # Add padding token if it doesn't exist
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        # Create text generation pipeline
        generator = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_length=512,  # Reasonable limit for summaries
            do_sample=True,
            temperature=0.9,  # Higher creativity for better expansion
            top_p=0.95,  # More diverse sampling
            top_k=50,  # Limit vocabulary for better quality
            repetition_penalty=1.2,  # Avoid repetition
            pad_token_id=tokenizer.eos_token_id
        )

        print("Model loaded successfully!")
        return generator

    except Exception as e:
        print(f"Error loading model: {e}")
        print("AI model is required for summarization. Please install transformers.")
        sys.exit(1)

def summarize_with_ai(generator, project_name: str, contents: List[str]) -> str:
    """
    Summarize standup contents using AI model.

    Args:
        generator: AI text generation pipeline
        project_name: Name of the project
        contents: List of work items

    Returns:
        Summarized work description
    """
    # Prepare input text with all work items
    work_items = "\n".join([f"- {item}" for item in contents])
    input_text = f"Project: {project_name}\nWork completed:\n{work_items}"

    # Create prompt
    prompt = get_initial_prompt() + "\n\n" + input_text

    try:
        # Generate summary with focused parameters
        result = generator(
            prompt,
            max_new_tokens=200,  # Reasonable limit for summaries
            num_return_sequences=1,
            temperature=0.9,  # High creativity for expansion
            do_sample=True,
            top_p=0.95,
            top_k=50,
            repetition_penalty=1.2,
            pad_token_id=generator.tokenizer.eos_token_id
        )

        # Extract generated text
        generated_text = result[0]['generated_text']

        # Extract only the summary part (after the prompt)
        if "Now transform these work items:" in generated_text:
            summary = generated_text.split("Now transform these work items:")[-1].strip()
        else:
            summary = generated_text[len(prompt):].strip()

        # Clean up the summary
        summary = summary.replace("Project:", "").replace("Work completed:", "").strip()

        # If summary is too short or just repeats input, try a different approach
        if len(summary) < 50 or "Project:" in summary:
            # Try a simpler prompt
            simple_prompt = f"Rewrite these work items professionally:\n{work_items}\n\nProfessional summary:"
            simple_result = generator(
                simple_prompt,
                max_new_tokens=150,
                temperature=0.9,
                do_sample=True,
                top_p=0.95,
                top_k=50,
                repetition_penalty=1.2,
                pad_token_id=generator.tokenizer.eos_token_id
            )
            summary = simple_result[0]['generated_text'].replace(simple_prompt, "").strip()

        return summary

    except Exception as e:
        print(f"Error in AI generation: {e}")
        raise e


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
        print(f"Processing standup {i+1}/{len(standups)}: {standup.get('title', 'Unknown')}")

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

        print(f"Summaries saved to {output_path}")

    except Exception as e:
        print(f"Error saving summaries: {e}")
        sys.exit(1)

def main():
    """Main function to run the standup summarization."""
    # Get project root directory (parent of src/)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_file = os.path.join(project_root, "logs", "standups.json")
    output_file = os.path.join(project_root, "logs", "standups-summarized.json")

    print("Starting Standup Summarization...")

    # Load standup data
    print(f"Loading standups from {input_file}...")
    standups = load_standups(input_file)
    print(f"Loaded {len(standups)} standups")

    # Setup AI model
    generator = setup_local_model()

    # Process standups
    print("Processing standups...")
    summarized_standups = process_standups(standups, generator)

    # Save summaries
    print("Saving summaries...")
    save_summaries(summarized_standups, output_file)

    print("Standup summarization completed successfully!")
    print(f"Output saved to: {output_file}")

if __name__ == "__main__":
    main()
