import json
from pathlib import Path


def convert_lists_to_tuples(d):
    if isinstance(d, dict):
        return {k: convert_lists_to_tuples(v) for k, v in d.items()}
    elif isinstance(d, list):
        # jeśli to wygląda jak zakres (2 liczby)
        if len(d) == 2 and all(isinstance(x, (int, float)) for x in d):
            return tuple(d)
        return [convert_lists_to_tuples(x) for x in d]
    else:
        return d

def get_archetype(file_name: str):

    base_dir = Path(__file__).resolve().parent
    file_path = base_dir / file_name

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    archetypes = convert_lists_to_tuples(data)

    return archetypes