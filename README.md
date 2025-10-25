# Notion Standup Script

A Python script that fetches all pages with status = "Done" from a Notion database and saves them to a JSON file.

## Features

- Fetches all pages with "Done" status from a Notion database
- Extracts detailed page properties and metadata
- Saves results to timestamped JSON files in `logs/work-done-today/`
- Handles pagination for large databases
- Supports various Notion property types (text, select, date, checkbox, etc.)

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Get your Notion integration token:
   - Go to [Notion Integrations](https://www.notion.so/my-integrations)
   - Create a new integration
   - Copy the "Internal Integration Token"

3. Get your database ID:
   - Open your Notion database in a web browser
   - Copy the database ID from the URL (the long string after the last `/` and before the `?`)

4. Share your database with the integration:
   - In your Notion database, click "Share" → "Add people, emails, groups, or integrations"
   - Add your integration

## Usage

### Method 1: Direct Command Line

```bash
python notion_standup.py --token YOUR_NOTION_TOKEN --database-id YOUR_DATABASE_ID
```

### Method 2: Using Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your actual values:
   ```
   NOTION_TOKEN=your_actual_token_here
   NOTION_DATABASE_ID=your_actual_database_id_here
   ```

3. Run the script:
   ```bash
   ./run_standup.sh
   ```

### Method 3: Programmatic Usage

```python
from notion_standup import NotionStandup

client = NotionStandup("your_token", "your_database_id")
output_file = client.run()
print(f"Results saved to: {output_file}")
```

### Optional Parameters

- `--output-dir`: Specify custom output directory (default: `logs/work-done-today`)

### Example

```bash
python notion_standup.py \
  --token "secret_abc123..." \
  --database-id "12345678-1234-1234-1234-123456789abc" \
  --output-dir "logs/work-done-today"
```

## Output

The script creates JSON files with the following structure:

```json
{
  "metadata": {
    "timestamp": "2024-01-15T10:30:00.000Z",
    "total_pages": 5,
    "database_id": "your-database-id"
  },
  "pages": [
    {
      "id": "page-id",
      "url": "https://notion.so/page-url",
      "created_time": "2024-01-15T09:00:00.000Z",
      "last_edited_time": "2024-01-15T10:00:00.000Z",
      "archived": false,
      "properties": {
        "Name": "Task Title",
        "Status": "Done",
        "Description": "Task description...",
        "Due Date": "2024-01-15",
        "Priority": "High"
      }
    }
  ]
}
```

## Files

- `notion_standup.py` - Main Python script
- `example_usage.py` - Example of programmatic usage
- `run_standup.sh` - Shell script for easy execution with environment variables
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variables template
- `README.md` - This documentation

## Requirements

- Python 3.7+
- Notion integration token
- Database with a "Status" property containing "Done" values
