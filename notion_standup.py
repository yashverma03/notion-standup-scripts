#!/usr/bin/env python3
"""
Notion Standup Script
Fetches all pages with status = "Done" from a Notion database and saves to JSON file.
"""

import os
import json
import requests
import sys
from datetime import datetime
from typing import Dict, List, Any


class NotionStandup:
    def __init__(self, notion_token: str, database_id: str):
        """
        Initialize the Notion Standup client.

        Args:
            notion_token: Notion integration token
            database_id: Notion database ID
        """
        self.notion_token = notion_token
        self.database_id = database_id
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {notion_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

    def fetch_done_pages(self) -> List[Dict[str, Any]]:
        """
        Fetch all pages from the database with status = "Done".

        Returns:
            List of page objects with their details
        """
        all_pages = []
        has_more = True
        start_cursor = None

        print("Fetching pages with status = 'Done'...")

        while has_more:
            # Prepare the request body for filtering
            request_body = {
                "filter": {
                    "property": "Status",
                    "select": {
                        "equals": "Done"
                    }
                },
                "sorts": [
                    {
                        "property": "Last edited time",
                        "direction": "descending"
                    }
                ]
            }

            if start_cursor:
                request_body["start_cursor"] = start_cursor

            try:
                response = requests.post(
                    f"{self.base_url}/databases/{self.database_id}/query",
                    headers=self.headers,
                    json=request_body
                )
                response.raise_for_status()

                data = response.json()
                pages = data.get("results", [])
                all_pages.extend(pages)

                has_more = data.get("has_more", False)
                start_cursor = data.get("next_cursor")

                print(f"Fetched {len(pages)} pages (total: {len(all_pages)})")

            except requests.exceptions.RequestException as e:
                print(f"Error fetching pages: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"Response: {e.response.text}")
                sys.exit(1)

        return all_pages

    def get_page_details(self, page_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific page.

        Args:
            page_id: The ID of the page to fetch details for

        Returns:
            Page details dictionary
        """
        try:
            response = requests.get(
                f"{self.base_url}/pages/{page_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching page details for {page_id}: {e}")
            return {}

    def extract_page_properties(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant properties from a Notion page.

        Args:
            page: Raw page object from Notion API

        Returns:
            Dictionary with extracted properties
        """
        properties = page.get("properties", {})

        # Extract common properties
        extracted = {
            "id": page.get("id"),
            "url": page.get("url"),
            "created_time": page.get("created_time"),
            "last_edited_time": page.get("last_edited_time"),
            "archived": page.get("archived", False),
            "properties": {}
        }

        # Extract specific properties based on common field names
        for prop_name, prop_data in properties.items():
            prop_type = prop_data.get("type")

            if prop_type == "title":
                title_array = prop_data.get("title", [])
                extracted["properties"][prop_name] = title_array[0].get("plain_text", "") if title_array else ""

            elif prop_type == "rich_text":
                rich_text_array = prop_data.get("rich_text", [])
                extracted["properties"][prop_name] = "".join([text.get("plain_text", "") for text in rich_text_array])

            elif prop_type == "select":
                select_obj = prop_data.get("select")
                extracted["properties"][prop_name] = select_obj.get("name", "") if select_obj else ""

            elif prop_type == "multi_select":
                multi_select_array = prop_data.get("multi_select", [])
                extracted["properties"][prop_name] = [item.get("name", "") for item in multi_select_array]

            elif prop_type == "date":
                date_obj = prop_data.get("date")
                extracted["properties"][prop_name] = date_obj.get("start", "") if date_obj else ""

            elif prop_type == "checkbox":
                extracted["properties"][prop_name] = prop_data.get("checkbox", False)

            elif prop_type == "number":
                extracted["properties"][prop_name] = prop_data.get("number")

            elif prop_type == "url":
                extracted["properties"][prop_name] = prop_data.get("url", "")

            elif prop_type == "email":
                extracted["properties"][prop_name] = prop_data.get("email", "")

            elif prop_type == "phone_number":
                extracted["properties"][prop_name] = prop_data.get("phone_number", "")

            else:
                # For other types, store the raw data
                extracted["properties"][prop_name] = prop_data

        return extracted

    def save_to_json(self, pages: List[Dict[str, Any]]) -> str:
        """
        Save pages to a JSON file.

        Args:
            pages: List of page objects to save

        Returns:
            Path to the saved JSON file
        """
        # Hardcoded output directory
        output_dir = "logs/work-done-today"

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"notion_done_pages_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)

        # Prepare data for JSON output
        output_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_pages": len(pages),
                "database_id": self.database_id
            },
            "pages": pages
        }

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            print(f"Successfully saved {len(pages)} pages to {filepath}")
            return filepath

        except Exception as e:
            print(f"Error saving to JSON: {e}")
            sys.exit(1)

    def run(self) -> str:
        """
        Main method to fetch done pages and save to JSON.

        Returns:
            Path to the saved JSON file
        """
        print("Starting Notion Standup Script...")
        print(f"Database ID: {self.database_id}")

        # Fetch all pages with status = "Done"
        raw_pages = self.fetch_done_pages()

        if not raw_pages:
            print("No pages found with status = 'Done'")
            return self.save_to_json([])

        print(f"Processing {len(raw_pages)} pages...")

        # Extract properties from each page
        processed_pages = []
        for i, page in enumerate(raw_pages, 1):
            print(f"Processing page {i}/{len(raw_pages)}: {page.get('id', 'unknown')}")
            extracted_page = self.extract_page_properties(page)
            processed_pages.append(extracted_page)

        # Save to JSON file
        return self.save_to_json(processed_pages)
