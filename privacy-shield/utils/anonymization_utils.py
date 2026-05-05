import re


def redact_text(original_text: str, entities_json: dict) -> tuple[str, dict]:
            """
            Redacts the original text by replacing sensitive information with placeholders based on the extracted entities.

            Args:
                original_text (str): The original text to be redacted.
                entities_json (dict): A dictionary containing the extracted entities categorized by their types.
            
            Returns:
                tuple[str, dict]: A tuple containing the redacted text and a mapping of placeholders to original values.
            """
            sorted_entities = _get_sorted_entities(entities_json)
            return _apply_masks(original_text, sorted_entities)

def _get_sorted_entities(entities_json: dict) -> list[tuple]:
    """
    Sorts the extracted entities by their length in descending order to ensure that longer matches are replaced before shorter ones.

    Args:
        entities_json (dict): A dictionary containing the extracted entities categorized by their types.

    Returns:
        list[tuple]: A list of tuples where each tuple contains an entity value and its corresponding category, sorted by the length of the entity value in descending order.
    """
    flat_entities = []
    for category, values in entities_json.items():
        if isinstance(values, list):
            for value in values:
                if len(str(value).strip()) > 2:
                    flat_entities.append((str(value), category))

    return sorted(flat_entities, key=lambda x: len(x[0]), reverse=True)

def _apply_masks(text: str, sorted_entities: list[tuple]) -> tuple[str, dict]:
    """
    Applies masks to the original text by replacing sensitive information with placeholders.

    Args:
        text (str): The original text to be redacted.
        sorted_entities (list[tuple]): A list of tuples containing the entity values and their corresponding categories, sorted by entity length.

    Returns:
        tuple[str, dict]: A tuple containing the redacted text and a mapping of placeholders to original values.
    """
    mapping = {}
    anonymized_text = text
    counters = {}

    for original_value, category in sorted_entities:
        if original_value in mapping.values():
            continue

        counters[category] = counters.get(category, 0) + 1
        label = f"[{category}_{counters[category]}]"
            
        mapping[label] = original_value
            
        pattern = re.compile(re.escape(original_value), re.IGNORECASE)
        anonymized_text = pattern.sub(label, anonymized_text)
           
    return anonymized_text, mapping