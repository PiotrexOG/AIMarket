import json
import statistics
from pathlib import Path
from typing import List, Dict
from pydantic import BaseModel
from datetime import datetime

# --- MAPOWANIE NAZW ---
# JSON (stary/nowy) <-> DTO (z serwisu)
METRIC_MAP = {
    "tech": "relative_technical_strength",
    "fund": "relative_fundamental_support",
    "val": "relative_valuation_sustainability",
    "risk": "relative_structural_risk",
    "conv": "relative_conviction",
    "asym": "relative_asymmetry_profile"
}

# Mapowanie prostych pól
PARAM_MAP = {
    "risk_tolerance": "risk_tolerance",
    "min_score": "min_score_threshold",
    "temp": "softmax_temp",
    "rebalance_range": "rebalance_threshold"
}

TIME_MAP = {
    "short": "short_term_weight",
    "medium": "medium_term_weight",
    "long": "long_term_weight"
}


def get_new_range(current_range, top_values, all_values, spread_factor=0.8):
    """
    current_range: [min, max]
    top_values: wartości parametrów dla top 30% portfeli
    all_values: wartości parametrów dla wszystkich portfeli
    spread_factor: 1.0 = zachowaj szerokość, < 1.0 = zawęź (skupienie), > 1.0 = rozszerz (eksploracja)
    """
    m_top = statistics.mean(top_values) if top_values else 0
    m_all = statistics.mean(all_values) if all_values else 0

    # 1. Obliczamy shift (całkowite przesunięcie)
    shift = (m_top - m_all)

    # 2. Parametry starego zakresu
    old_min, old_max = current_range
    old_width = old_max - old_min
    old_center = (old_min + old_max) / 2

    # 3. Nowy środek i nowa szerokość
    new_center = old_center + shift
    new_width = old_width * spread_factor

    # 4. Wyznaczenie nowych krawędzi
    new_min = new_center - (new_width / 2)
    new_max = new_center + (new_width / 2)

    # Korrekta, żeby nie wyjść poniżej 0 (możesz też dodać limit górny np. 1.0)
    if new_min < 0:
        # Jeśli min dobija do zera, możemy albo uciąć, albo przesunąć zakres w górę
        new_min = 0
        new_max = new_min + new_width

    return [round(new_min, 4), round(new_max, 4)]


def process_and_print_results(summaries: List, original_config: Dict):
    new_config = {}

    # Grupowanie
    archetypes_data = {}
    for res in summaries:
        key = res.archetype_key
        if key not in archetypes_data:
            archetypes_data[key] = []
        archetypes_data[key].append(res)

    for archetype_key, portfolios in archetypes_data.items():
        if archetype_key not in original_config:
            continue

        print(f"\n{'=' * 80}")
        print(f" ANALIZA ARCHETYPU: {archetype_key.upper()}")
        print(f"{'=' * 80}")

        # Sortowanie i podział na TOP 30%
        portfolios.sort(key=lambda x: x.change_ratio, reverse=True)
        top_count = max(1, int(len(portfolios) * 0.3))
        top_portfolios = portfolios[:top_count]

        orig = original_config[archetype_key]
        new_archetype = {"time_weights": {}, "metric_weights": {}}

        print(f"{'Parametr':<25} | {'Śr. Ogółu':<10} | {'Śr. Top 30%':<12} | {'Stary Zakres':<15} | {'Nowy Zakres'}")
        print("-" * 80)

        # 1. Przetwarzanie TIME WEIGHTS
        for json_key, dto_key in TIME_MAP.items():
            all_vals = [getattr(p, dto_key) for p in portfolios]
            top_vals = [getattr(p, dto_key) for p in top_portfolios]

            old_range = orig["time_weights"][json_key]
            new_range = get_new_range(old_range, top_vals, all_vals)
            new_archetype["time_weights"][json_key] = new_range

            print(
                f"{'time_' + json_key:<25} | {statistics.mean(all_vals):.4f}     | {statistics.mean(top_vals):.4f}      | {str(old_range):<15} | {str(new_range)}")

        # 2. Przetwarzanie METRIC WEIGHTS
        for json_key, dto_key in METRIC_MAP.items():
            all_vals = [p.metric_weights[dto_key] for p in portfolios]
            top_vals = [p.metric_weights[dto_key] for p in top_portfolios]

            old_range = orig["metric_weights"][json_key]
            new_range = get_new_range(old_range, top_vals, all_vals)
            new_archetype["metric_weights"][json_key] = new_range

            print(
                f"{'metric_' + json_key:<25} | {statistics.mean(all_vals):.4f}     | {statistics.mean(top_vals):.4f}      | {str(old_range):<15} | {str(new_range)}")

        # 3. Przetwarzanie POZOSTAŁYCH PARAMETRÓW
        for json_key, dto_key in PARAM_MAP.items():
            all_vals = [getattr(p, dto_key) for p in portfolios]
            top_vals = [getattr(p, dto_key) for p in top_portfolios]

            old_range = orig[json_key]
            new_range = get_new_range(old_range, top_vals, all_vals)
            new_archetype[json_key] = new_range

            print(
                f"{json_key:<25} | {statistics.mean(all_vals):.4f}     | {statistics.mean(top_vals):.4f}      | {str(old_range):<15} | {str(new_range)}")

        new_config[archetype_key] = new_archetype


        text = json.dumps(new_config, indent=4)

        filename = f"new_archetypes_normalized.json"

        base_dir = Path(__file__).resolve().parent
        file_path = base_dir / filename

        # usuwa newline w prostych listach
        import re
        text = re.sub(r"\[\s+([^\[\]]+?)\s+\]", lambda m: "[" + " ".join(m.group(1).split()) + "]", text)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)

    return new_config