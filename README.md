# Notion Standup Scripts

Automated script to fetch daily standups from Notion and generate summaries using local AI models.

## Features

- Fetch completed tasks from Notion database
- Extract detailed page content (checkboxes, bullet points, text)
- Generate AI-powered summaries of daily work
- Generate prompts for external AI services

## Requirements

- Python 3.8+
- Notion API integration
- Local AI model (or compatible model)

## Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd notion-standup-scripts
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv .venv
   ```

3. **Activate the virtual environment:**
   ```bash
   source .venv/bin/activate
   ```

4. **Install required packages:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add:
   - `NOTION_TOKEN`: Your Notion integration token
   - `NOTION_DATABASE_ID`: The ID of your standup database
   - `AI_MODEL_NAME`: The AI model to use (e.g., `gpt2`, `distilgpt2`)

## Usage

### Running All Scripts

Run the complete workflow (fetch standups and generate summaries):

```bash
./src/main.sh
```

Or manually:
```bash
source .venv/bin/activate
python src/get_standups.py
python src/summarize_standups.py
```

### Individual Scripts

#### 1. Fetch Standups (`src/get_standups.py`)

Fetches completed tasks from your Notion database and saves them to `logs/standups.json`.

```bash
python src/get_standups.py
```

**Output:** `logs/standups.json`

**What it does:**
- Connects to Notion API
- Queries the database for pages with "Status" = "Done"
- Extracts page properties (id, title, projectName)
- Recursively fetches all content blocks (checkboxes, bullet points, text)
- Saves structured JSON data

#### 2. Generate Summaries (`src/summarize_standups.py`)

Summarizes the fetched standups using a local AI model.

```bash
python src/summarize_standups.py
```

**Input:** `logs/standups.json`
**Output:** `logs/standups-summarized.json`

**What it does:**
- Loads standup data from `logs/standups.json`
- Generates detailed, professional summaries using AI
- Expands short phrases into comprehensive accomplishments
- Saves project-wise summaries

#### 3. Generate Prompt (`src/standup_prompt.py`)

Generates a complete prompt for external AI services.

```bash
python src/standup_prompt.py
```

**Input:** `logs/standups.json`
**Output:** `logs/standup-prompt.txt`

**What it does:**
- Loads standup data from `logs/standups.json`
- Combines initial instructions with standup data
- Adds response format requirements
- Saves to text file and copies to clipboard
