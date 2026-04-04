import json
import os
from typing import List, Dict, Any

def load_json(filepath: str) -> Any:
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                return None
            return json.loads(content)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading JSON from {filepath}: {e}")
        return None

def save_json(filepath: str, data: Any):
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"Error saving JSON to {filepath}: {e}")

def flatten_dict_list(data_list: List[Dict[str, Any]], key_field: str) -> Dict[str, Dict[str, Any]]:
    flat_dict = {}
    if not isinstance(data_list, list):
        print("Warning: flatten_dict_list expects a list.")
        return {}
    for item in data_list:
        if not isinstance(item, dict):
            print(f"Warning: Skipped non-dictionary item in list: {item}")
            continue
        key_value = item.get(key_field)
        if key_value is not None:
            if key_value in flat_dict:
                print(f"Warning: Duplicate key '{key_value}' found in list for field '{key_field}'. Overwriting.")
            flat_dict[key_value] = item
        else:
            print(f"Warning: Item missing key field '{key_field}': {item}")
    return flat_dict

def unflatten_dict(data_dict: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not isinstance(data_dict, dict):
        print("Warning: unflatten_dict expects a dictionary.")
        return []
    return list(data_dict.values())
