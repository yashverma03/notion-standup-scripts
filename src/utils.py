#!/usr/bin/env python3
"""
Common utility functions for the Notion standup scripts.
"""

import os
import sys


def get_env_or_throw(env_var: str) -> str:
    """
    Get environment variable or throw an error with auto-generated message.

    Args:
        env_var: Environment variable name

    Returns:
        Environment variable value

    Raises:
        SystemExit: If environment variable is not set
    """
    value = os.getenv(env_var)
    if not value:
        print(f"Error: {env_var} environment variable is required")
        sys.exit(1)
    return value
