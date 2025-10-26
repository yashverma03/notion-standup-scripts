#!/bin/bash

# Activate virtual environment
source .venv/bin/activate

# Run get_standups.py
python src/get_standups.py

# Run standup-prompt.py
python src/standup_prompt.py
