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
from dotenv import load_dotenv
from utils import get_env_or_throw

# Load environment variables from .env file
load_dotenv()


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
                    "status": {
                        "equals": "Done"
                    }
                }
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
        Get detailed information for a specific page with content.

        Args:
            page_id: The ID of the page to fetch details for

        Returns:
            Page details dictionary with content
        """
        try:
            response = requests.get(
                f"{self.base_url}/pages/{page_id}",
                headers=self.headers
            )
            response.raise_for_status()
            page_data = response.json()

            # Extract detailed properties and content
            return self.extract_page_details(page_data)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching page details for {page_id}: {e}")
            return {}

    def get_page_blocks(self, page_id: str) -> List[Dict[str, Any]]:
        """
        Get all blocks (content) from a specific page.

        Args:
            page_id: The ID of the page to fetch blocks for

        Returns:
            List of block objects
        """
        all_blocks = []
        has_more = True
        start_cursor = None

        while has_more:
            try:
                url = f"{self.base_url}/blocks/{page_id}/children"
                params = {}
                if start_cursor:
                    params["start_cursor"] = start_cursor

                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()

                data = response.json()
                blocks = data.get("results", [])
                all_blocks.extend(blocks)

                has_more = data.get("has_more", False)
                start_cursor = data.get("next_cursor")

            except requests.exceptions.RequestException as e:
                print(f"Error fetching blocks for page {page_id}: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"Response: {e.response.text}")
                break

        return all_blocks

    def get_all_blocks_recursive(self, page_id: str) -> List[Dict[str, Any]]:
        """
        Get all blocks from a page recursively, including all children.

        Args:
            page_id: The ID of the page to fetch blocks for

        Returns:
            List of all block objects in order
        """
        all_blocks = []
        has_more = True
        start_cursor = None

        while has_more:
            try:
                url = f"{self.base_url}/blocks/{page_id}/children"
                params = {}
                if start_cursor:
                    params["start_cursor"] = start_cursor

                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()

                data = response.json()
                blocks = data.get("results", [])

                # Process each block and its children
                for block in blocks:
                    all_blocks.append(block)

                    # If block has children, fetch them recursively
                    if block.get("has_children", False):
                        child_blocks = self.get_all_blocks_recursive(block.get("id"))
                        all_blocks.extend(child_blocks)

                has_more = data.get("has_more", False)
                start_cursor = data.get("next_cursor")

            except requests.exceptions.RequestException as e:
                print(f"Error fetching blocks for page {page_id}: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"Response: {e.response.text}")
                break

        return all_blocks

    def extract_block_content(self, block: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract text content from a block based on its type.

        Args:
            block: Block object from Notion API

        Returns:
            Dictionary with extracted content
        """
        block_type = block.get("type", "unknown")
        block_id = block.get("id", "")
        created_time = block.get("created_time", "")
        last_edited_time = block.get("last_edited_time", "")

        extracted = {
            "id": block_id,
            "type": block_type,
            "created_time": created_time,
            "last_edited_time": last_edited_time,
            "content": "",
            "checked": None,
            "has_children": block.get("has_children", False)
        }

        # Extract content based on block type
        if block_type == "to_do":
            to_do_data = block.get("to_do", {})
            rich_text = to_do_data.get("rich_text", [])
            content = "".join([text.get("plain_text", "") for text in rich_text])
            extracted["content"] = content
            extracted["checked"] = to_do_data.get("checked", False)

        elif block_type == "paragraph":
            paragraph_data = block.get("paragraph", {})
            rich_text = paragraph_data.get("rich_text", [])
            content = "".join([text.get("plain_text", "") for text in rich_text])
            extracted["content"] = content

        elif block_type == "heading_1":
            heading_data = block.get("heading_1", {})
            rich_text = heading_data.get("rich_text", [])
            content = "".join([text.get("plain_text", "") for text in rich_text])
            extracted["content"] = content

        elif block_type == "heading_2":
            heading_data = block.get("heading_2", {})
            rich_text = heading_data.get("rich_text", [])
            content = "".join([text.get("plain_text", "") for text in rich_text])
            extracted["content"] = content

        elif block_type == "heading_3":
            heading_data = block.get("heading_3", {})
            rich_text = heading_data.get("rich_text", [])
            content = "".join([text.get("plain_text", "") for text in rich_text])
            extracted["content"] = content

        elif block_type == "bulleted_list_item":
            list_data = block.get("bulleted_list_item", {})
            rich_text = list_data.get("rich_text", [])
            content = "".join([text.get("plain_text", "") for text in rich_text])
            extracted["content"] = content

        elif block_type == "numbered_list_item":
            list_data = block.get("numbered_list_item", {})
            rich_text = list_data.get("rich_text", [])
            content = "".join([text.get("plain_text", "") for text in rich_text])
            extracted["content"] = content

        elif block_type == "toggle":
            toggle_data = block.get("toggle", {})
            rich_text = toggle_data.get("rich_text", [])
            content = "".join([text.get("plain_text", "") for text in rich_text])
            extracted["content"] = content

        elif block_type == "quote":
            quote_data = block.get("quote", {})
            rich_text = quote_data.get("rich_text", [])
            content = "".join([text.get("plain_text", "") for text in rich_text])
            extracted["content"] = content

        elif block_type == "code":
            code_data = block.get("code", {})
            rich_text = code_data.get("rich_text", [])
            content = "".join([text.get("plain_text", "") for text in rich_text])
            extracted["content"] = content
            extracted["language"] = code_data.get("language", "")

        elif block_type == "callout":
            callout_data = block.get("callout", {})
            rich_text = callout_data.get("rich_text", [])
            content = "".join([text.get("plain_text", "") for text in rich_text])
            extracted["content"] = content
            extracted["icon"] = callout_data.get("icon", {})

        else:
            # For other block types, try to extract any rich_text content
            for key, value in block.items():
                if isinstance(value, dict) and "rich_text" in value:
                    rich_text = value.get("rich_text", [])
                    content = "".join([text.get("plain_text", "") for text in rich_text])
                    if content:
                        extracted["content"] = content
                        break

        return extracted

    def extract_page_properties(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract only id, title, and projectName from a Notion page (for fetch_done_pages).

        Args:
            page: Raw page object from Notion API

        Returns:
            Dictionary with id, title, and projectName
        """
        properties = page.get("properties", {})
        page_id = page.get("id")

        # Extract only the 3 required fields
        extracted = {
            "id": page_id,
            "title": "",
            "projectName": ""
        }

        # Extract title from Name property
        name_prop = properties.get("Name", {})
        if name_prop.get("type") == "title":
            title_array = name_prop.get("title", [])
            extracted["title"] = title_array[0].get("plain_text", "") if title_array else ""

        # Extract project name from Project property
        project_prop = properties.get("Project", {})
        if project_prop.get("type") == "select":
            select_obj = project_prop.get("select")
            extracted["projectName"] = select_obj.get("name", "") if select_obj else ""

        return extracted

    def extract_page_details(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract detailed properties and content from a Notion page (for get_page_details).

        Args:
            page: Raw page object from Notion API

        Returns:
            Dictionary with detailed properties and content
        """
        properties = page.get("properties", {})
        page_id = page.get("id")

        # Extract common properties
        extracted = {
            "id": page_id,
            "url": page.get("url"),
            "created_time": page.get("created_time"),
            "last_edited_time": page.get("last_edited_time"),
            "archived": page.get("archived", False),
            "properties": {},
            "content": []
        }

        # Fetch and extract block content
        if page_id:
            print(f"  Fetching blocks for page {page_id}...")
            blocks = self.get_page_blocks(page_id)
            for block in blocks:
                block_content = self.extract_block_content(block)
                if block_content["content"]:  # Only include blocks with content
                    extracted["content"].append(block_content)

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

    def extract_simple_content(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract id, title, projectName, and contents (checkbox, bullet points, normal text only).

        Args:
            page: Raw page object from Notion API

        Returns:
            Dictionary with id, title, projectName, and contents
        """
        properties = page.get("properties", {})
        page_id = page.get("id")

        # Extract basic info
        extracted = {
            "id": page_id,
            "title": "",
            "projectName": "",
            "contents": []
        }

        # Extract title from Name property
        name_prop = properties.get("Name", {})
        if name_prop.get("type") == "title":
            title_array = name_prop.get("title", [])
            extracted["title"] = title_array[0].get("plain_text", "") if title_array else ""

        # Extract project name from Project property
        project_prop = properties.get("Project", {})
        if project_prop.get("type") == "select":
            select_obj = project_prop.get("select")
            extracted["projectName"] = select_obj.get("name", "") if select_obj else ""

        # Fetch and extract only specific content types recursively
        if page_id:
            print(f"  Fetching content for page {page_id}...")
            blocks = self.get_all_blocks_recursive(page_id)
            for block in blocks:
                block_content = self.extract_block_content(block)
                content = block_content.get("content", "")
                block_type = block_content.get("type", "")

                if not content:
                    continue

                # Add all content types to single array
                if block_type in ["to_do", "bulleted_list_item", "numbered_list_item", "paragraph", "heading_1", "heading_2", "heading_3"]:
                    extracted["contents"].append(content)

        return extracted

    def save_to_json(self, pages: List[Dict[str, Any]]) -> str:
        """
        Save pages to a JSON file.

        Args:
            pages: List of page objects to save

        Returns:
            Path to the saved JSON file
        """
        # Get project root directory (parent of src/)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(project_root, "logs")
        filename = "standups.json"
        filepath = os.path.join(output_dir, filename)

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(pages, f, indent=2, ensure_ascii=False)

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

        # Extract properties and content from each page
        processed_pages = []
        for i, page in enumerate(raw_pages, 1):
            print(f"Processing page {i}/{len(raw_pages)}: {page.get('id', 'unknown')}")
            extracted_page = self.extract_simple_content(page)
            processed_pages.append(extracted_page)

        # Save to JSON file
        return self.save_to_json(processed_pages)


def main():
    """Main function to run the script using environment variables."""
    # Get credentials from environment variables
    notion_token = get_env_or_throw("NOTION_TOKEN")
    database_id = get_env_or_throw("NOTION_DATABASE_ID")

    # Create and run the Notion client
    client = NotionStandup(notion_token, database_id)

    try:
        output_file = client.run()
        print(f"\nScript completed successfully!")
        print(f"Output saved to: {output_file}")

    except Exception as e:
        print(f"Script failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
