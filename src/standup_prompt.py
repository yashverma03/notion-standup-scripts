#!/usr/bin/env python3
"""
Standup Prompt Generator
Generates prompts for AI summarization of standup data.
"""

import json
import os
import sys
from typing import Dict, List, Any
from dotenv import load_dotenv
from utils import get_env_or_throw
import pyperclip

# Load environment variables
load_dotenv()

class StandupPromptGenerator:
    """Class to generate prompts for standup summarization."""

    def get_initial_prompt(self) -> str:
        """
        Get the initial prompt for standup summarization.

        Returns:
            Initial prompt string
        """
        return """
Complete the following work items into proper sentences.
Keep ticket numbers at the beginning.
Do not add extra details.
Do NOT add credentials, API keys, passwords, or sensitive environment values or any URLs.

Format the output as a single string with bullet points separated by newlines.
Each bullet point should start with a dash (-)

Now summarize the following standup data:"""

    def get_response_format_prompt(self) -> str:
        """
        Get the response format instructions.

        Returns:
            Response format prompt string
        """
        return """

Response Format:
The response should be in text with bullet points organized by project.

Format for each project:
<Project Name>

- Point 1 describing the work accomplished
- Point 2 describing the work accomplished
- Point 3 describing the work accomplished

Example output:

TenantPay

- Resolved critical bug in rental payment processing system
- Implemented robust error handling for transaction failures
- Optimized database queries for improved performance

Gigworks

- Fixed UI rendering issue affecting user interface
- Added comprehensive filtering mechanism for data tables
- Conducted thorough testing of new feature implementation"""

    def format_standup_data(self, standups: List[Dict[str, Any]]) -> str:
        """
        Format standup data for the prompt.

        Args:
            standups: List of standup dictionaries

        Returns:
            Formatted string with standup data
        """
        formatted_data = []

        for standup in standups:
            project_name = standup.get('projectName', 'Unknown Project')
            contents = standup.get('contents', [])

            project_data = f"Project: {project_name}\nWork completed:\n"
            project_data += "\n".join([f"- {item}" for item in contents])
            formatted_data.append(project_data)

        return "\n\n---\n\n".join(formatted_data)

    def generate_prompt(self, standups: List[Dict[str, Any]]) -> str:
        """
        Generate the complete prompt for AI summarization.

        Args:
            standups: List of standup dictionaries

        Returns:
            Complete prompt string
        """
        # Get initial prompt
        initial_prompt = self.get_initial_prompt()

        # Format standup data
        formatted_data = self.format_standup_data(standups)

        # Get response format
        response_format = self.get_response_format_prompt()

        # Combine all parts
        complete_prompt = f"{initial_prompt}\n\n{formatted_data}\n{response_format}"

        return complete_prompt

    def load_standups(self, file_path: str) -> List[Dict[str, Any]]:
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

    def save_prompt(self, prompt: str, output_path: str) -> None:
        """
        Save the generated prompt to a text file.

        Args:
            prompt: The generated prompt
            output_path: Path to save the prompt file
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(prompt)

            print(f"Prompt saved to {output_path}")

        except Exception as e:
            print(f"Error saving prompt: {e}")
            sys.exit(1)

    def copy_to_clipboard(self, text: str) -> None:
        """
        Copy text to clipboard using pyperclip.

        Args:
            text: The text to copy to clipboard
        """
        try:
            pyperclip.copy(text)
            print("✓ Copied to clipboard")
        except Exception as e:
            print(f"Error copying to clipboard: {e}")

def main():
    """Main function to generate and save the prompt."""
    # Get project root directory (parent of src/)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_file = os.path.join(project_root, "logs", "standups.json")
    output_file = os.path.join(project_root, "logs", "standup-prompt.txt")

    # Load standup data
    generator = StandupPromptGenerator()
    print(f"Loading standups from {input_file}...")
    standups = generator.load_standups(input_file)
    print(f"Loaded {len(standups)} standups")

    # Generate prompt
    print("Generating prompt...")
    complete_prompt = generator.generate_prompt(standups)

    # Save prompt
    print("Saving prompt...")
    generator.save_prompt(complete_prompt, output_file)

    print("\n=== GENERATED PROMPT ===")
    print(complete_prompt)
    print("=== END PROMPT ===")

    print(f"\nPrompt saved to {output_file}")

    # Copy to clipboard
    generator.copy_to_clipboard(complete_prompt)

if __name__ == "__main__":
    main()
