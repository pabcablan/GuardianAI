import json
import logging
import re


LOGGER = logging.getLogger(__name__)


def extract_json_safely(text: str) -> dict:
    """Extract the first JSON object found in a raw model response.

    Args:
        text (str): Raw text returned by the language model.

    Returns:
        dict: Parsed JSON object, or an empty dict if parsing fails.
    """
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {}
    except json.JSONDecodeError:
        LOGGER.warning("The model response did not contain valid JSON.")
        return {}
