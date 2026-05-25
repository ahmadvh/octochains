import json
import re
import logging
from pydantic import BaseModel, ValidationError

def parse_and_validate_json(raw_text: str, target_class):
    """
    1. Removes LLM 'thinking' traces (e.g., <think> tags).
    2. Extracts the first JSON object '{ ... }' from the text.
    3. Parses it into a dictionary.
    4. Validates natively against Pydantic models (or standard classes).
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
        # If target_class is a Pydantic model, use its native validation engine
        if issubclass(target_class, BaseModel):
            return target_class.model_validate(data)
        
        # Fallback for standard classes 
        return target_class(**data)
        
    except ValidationError as e:
        logging.error(f"Pydantic schema validation failed for {target_class.__name__}:\n{e}")
        raise ValueError(f"Schema validation failed: {e.errors()}")
    except Exception as e:
        logging.error(f"Validation against {target_class.__name__} failed: {e}")
        raise ValueError(f"Schema validation failed: {e}")