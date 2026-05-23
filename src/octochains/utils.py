import json
import re
import logging

def parse_and_validate_json(raw_text: str, target_class):
    """
    1. Removes LLM 'thinking' traces (e.g., <think> tags).
    2. Extracts the first JSON object '{ ... }' from the text.
    3. Parses it into a dictionary.
    4. Validates against the target class using its from_dict method.
    """
    cleaned_text = re.sub(r'<think>.*?(?:</think>|$)', '', raw_text, flags=re.DOTALL)
    
    match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
    if not match:
        logging.error("Failed to find JSON block in LLM response.")
        raise ValueError("No valid JSON structure detected in the response.")
    
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as e:
        logging.error(f"JSON decoding failed: {e}")
        raise ValueError(f"Malformed JSON: {e}")
    
    try:
        instance = target_class.from_dict(data)
        return instance
    except Exception as e:
        logging.error(f"Validation against {target_class.__name__} failed: {e}")
        # CHANGED: Raise the error so the Aggregator's try/except block catches it
        raise ValueError(f"Schema validation failed: {e}")