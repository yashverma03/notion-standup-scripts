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
        Text generation pipeline
    """
    try:
        # Use a smaller, efficient model for local processing
        model_name = "microsoft/DialoGPT-medium"

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
            max_length=10240,  # Very high limit for extensive output
            do_sample=True,
            temperature=0.8,  # Slightly higher for more creative expansion
            top_p=0.9,
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
        # Generate summary with very high token limit for extensive output
        result = generator(
            prompt,
            max_new_tokens=4000,  # Very high limit for extensive summaries
            num_return_sequences=1,
            temperature=0.8,  # Higher for more creative expansion
            do_sample=True,
            pad_token_id=generator.tokenizer.eos_token_id
        )

        # Extract generated text
        generated_text = result[0]['generated_text']

        # Extract only the summary part (after the prompt)
        if "Now summarize the following standup data:" in generated_text:
            summary = generated_text.split("Now summarize the following standup data:")[-1].strip()
        else:
            summary = generated_text[len(prompt):].strip()

        # Clean up the summary
        summary = summary.replace("Project:", "").replace("Work completed:", "").strip()
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
    input_file = "logs/standups.json"
    output_file = "logs/standups-summarized.json"

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
