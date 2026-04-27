"""
Defines utility functions for handling JSON data, particularly for safely extracting JSON objects from text that may contain additional content. 
"""

import json
import re
from typing import Dict, Any


def extract_json_safely(text: str) -> Dict[str, Any]:
    """
    Attempts to extract and parse a JSON object from a string.
    
    Args:
        text (str): The raw text potentially containing JSON.
        
    Returns:
        Dict[str, Any]: The parsed JSON object or an empty dict if extraction fails.
    """
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {}
    except json.JSONDecodeError:
        print("ERROR: The LLM did not return a valid JSON.")
        return {}