import json
from pathlib import Path


def convert_struct_to_ranges(d):
    if isinstance(d, dict):
        # Sprawdzamy, czy słownik ma strukturę mean/spread
        if "mean" in d and "spread" in d:
            low = d["mean"] - d["spread"]
            high = d["mean"] + d["spread"]
            # Zwracamy zaokrąglony przedział jako krotkę (tuple)
            return (round(low, 4), round(high, 4))

        # Jeśli to zwykły słownik (np. cały profil), idziemy głębiej
        return {k: convert_struct_to_ranges(v) for k, v in d.items()}

    elif isinstance(d, list):
        return [convert_struct_to_ranges(x) for x in d]

    else:
        return d

def get_archetype(file_name: str):

    base_dir = Path(__file__).resolve().parent
    file_path = base_dir / file_name

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    archetypes = convert_struct_to_ranges(data)

    print(archetypes)

    return archetypes