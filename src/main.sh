#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Get the project root (parent directory of src)
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Activate virtual environment
source "$PROJECT_ROOT/.venv/bin/activate"

# Run get_standups.py
python "$PROJECT_ROOT/src/get_standups.py"

# Run standup-prompt.py
python "$PROJECT_ROOT/src/standup_prompt.py"
