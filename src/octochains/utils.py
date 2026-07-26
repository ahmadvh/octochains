import json
import re
import logging
from pydantic import BaseModel, ValidationError


def parse_and_validate_json(raw_text: str, target_class):
    """
    1. Removes LLM 'thinking' traces (e.g., <think> tags).
    2. Safely extracts JSON — checks for a markdown ```json block first,
       then falls back to scanning for the first substring that is
       structurally valid JSON (with trailing-comma repair attempted at
       each candidate position, before moving to the next).
    3. Auto-repairs common LLM syntax errors (trailing commas).
    4. Uses Pydantic's native, high-speed JSON validation.
    """
    cleaned_text = re.sub(r'<think>.*?(?:</think>|$)', '', raw_text, flags=re.DOTALL)

    fence_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', cleaned_text, re.DOTALL)

    if fence_match:
        json_str = re.sub(r',\s*([\]}])', r'\1', fence_match.group(1))
    else:
        decoder = json.JSONDecoder()
        search_pos = 0
        json_str = None

        while True:
            start_idx = cleaned_text.find('{', search_pos)
            if start_idx == -1:
                logging.error("Failed to find JSON block in LLM response.")
                raise ValueError("No valid JSON structure detected in the response.")

            try:
                _, end_idx = decoder.raw_decode(cleaned_text, start_idx)
                json_str = cleaned_text[start_idx:end_idx]
                break
            except json.JSONDecodeError:
                pass

            try:
                repaired = re.sub(r',\s*([\]}])', r'\1', cleaned_text[start_idx:])
                data, _ = decoder.raw_decode(repaired)
                json_str = json.dumps(data)
                break
            except json.JSONDecodeError:
                pass

            search_pos = start_idx + 1

    try:
        if issubclass(target_class, BaseModel):
            return target_class.model_validate_json(json_str)
        data = json.loads(json_str)
        return target_class(**data)

    except ValidationError as e:
        logging.error(f"Pydantic schema validation failed for {target_class.__name__}:\n{e}")
        raise ValueError(f"Schema validation failed: {e.errors()}")
    except json.JSONDecodeError as e:
        logging.error(f"JSON decoding failed: {e}\nExtracted string: {json_str}")
        raise ValueError(f"Malformed JSON: {e}")
    except Exception as e:
        logging.error(f"Validation against {target_class.__name__} failed: {e}")
        raise ValueError(f"Schema validation failed: {e}")

