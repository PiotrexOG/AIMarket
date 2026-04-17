ARCHETYPES = {
    "benchmark": {  # Kup po równo i trzymaj
        "time_weights": {"short": (0, 0), "medium": (0, 0), "long": (0, 0)},
        "metric_weights": {"tech": (0, 0), "fund": (0, 0), "val": (0, 0), "risk": (0, 0), "conv": (0, 0), "asym": (0, 0)},
        "risk_tolerance": (0, 0), "min_score": (0, 0), "temp": (0, 0),
        "rebalance_range": (0, 0)
    },
    "conservative_grandpa": {  # Skrajnie bezpieczny, tylko long-term
        "time_weights": {"short": (0.0, 0.05), "medium": (0.1, 0.2), "long": (0.75, 0.9)},
        "metric_weights": {"tech": (0.0, 0.05), "fund": (0.4, 0.6), "val": (0.3, 0.4), "risk": (0.1, 0.2), "conv": (0.0, 0.05), "asym": (0.0, 0.05)},
        "risk_tolerance": (0.1, 0.3), "min_score": (6.0, 7.5), "temp": (1.5, 2.0),
        "rebalance_range": (0.05, 0.10)
    },
    "value_hunter": {  # Szuka niedoszacowanych perełek
        "time_weights": {"short": (0.05, 0.15), "medium": (0.3, 0.4), "long": (0.5, 0.6)},
        "metric_weights": {"tech": (0.05, 0.1), "fund": (0.3, 0.4), "val": (0.4, 0.5), "risk": (0.05, 0.1), "conv": (0.05, 0.1), "asym": (0.05, 0.1)},
        "risk_tolerance": (0.4, 0.6), "min_score": (5.0, 6.5), "temp": (1.0, 1.5),
        "rebalance_range": (0.03, 0.06)
    },
    "degen_trader": {  # Agresywny, techniczny, krótkoterminowy
        "time_weights": {"short": (0.7, 0.9), "medium": (0.1, 0.2), "long": (0.0, 0.05)},
        "metric_weights": {"tech": (0.4, 0.6), "fund": (0.0, 0.05), "val": (0.0, 0.05), "risk": (0.05, 0.1), "conv": (0.1, 0.2), "asym": (0.2, 0.4)},
        "risk_tolerance": (0.9, 1.0), "min_score": (2.0, 4.0), "temp": (0.3, 0.6),
        "rebalance_range": (0.005, 0.015)
    },
    "growth_enthusiast": {  # Stawia na momentum i przyszłość
        "time_weights": {"short": (0.2, 0.3), "medium": (0.4, 0.5), "long": (0.2, 0.4)},
        "metric_weights": {"tech": (0.2, 0.3), "fund": (0.2, 0.3), "val": (0.05, 0.15), "risk": (0.1, 0.2), "conv": (0.1, 0.2), "asym": (0.2, 0.3)},
        "risk_tolerance": (0.7, 0.85), "min_score": (4.0, 5.5), "temp": (0.8, 1.2),
        "rebalance_range": (0.02, 0.04)
    },
    "risk_manager": {  # Priorytetem jest ochrona kapitału (structural risk)
        "time_weights": {"short": (0.1, 0.2), "medium": (0.4, 0.4), "long": (0.4, 0.5)},
        "metric_weights": {"tech": (0.05, 0.1), "fund": (0.1, 0.2), "val": (0.1, 0.2), "risk": (0.5, 0.7), "conv": (0.05, 0.1), "asym": (0.05, 0.1)},
        "risk_tolerance": (0.2, 0.4), "min_score": (5.5, 7.0), "temp": (1.2, 1.6),
        "rebalance_range": (0.01, 0.03)
    },
    "balanced_pensioner": {  # Klasyczne 60/40, umiarkowany spokój
        "time_weights": {"short": (0.1, 0.2), "medium": (0.4, 0.5), "long": (0.3, 0.4)},
        "metric_weights": {"tech": (0.1, 0.2), "fund": (0.2, 0.3), "val": (0.2, 0.3), "risk": (0.1, 0.2), "conv": (0.1, 0.15), "asym": (0.05, 0.15)},
        "risk_tolerance": (0.4, 0.6), "min_score": (4.5, 5.5), "temp": (1.0, 1.2),
        "rebalance_range": (0.04, 0.07)
    },
    "conviction_heavy": {  # Gra tylko pod to, w co mocno wierzy
        "time_weights": {"short": (0.05, 0.1), "medium": (0.2, 0.3), "long": (0.6, 0.75)},
        "metric_weights": {"tech": (0.05, 0.1), "fund": (0.1, 0.2), "val": (0.05, 0.1), "risk": (0.05, 0.1), "conv": (0.5, 0.7), "asym": (0.1, 0.2)},
        "risk_tolerance": (0.6, 0.8), "min_score": (6.5, 8.0), "temp": (0.4, 0.7),
        "rebalance_range": (0.06, 0.12)
    },
    "asymmetry_seeker": {  # Szuka układów o małym ryzyku i wielkim potencjale (black swans)
        "time_weights": {"short": (0.1, 0.2), "medium": (0.3, 0.4), "long": (0.4, 0.5)},
        "metric_weights": {"tech": (0.1, 0.15), "fund": (0.05, 0.1), "val": (0.1, 0.2), "risk": (0.1, 0.2), "conv": (0.1, 0.2), "asym": (0.4, 0.6)},
        "risk_tolerance": (0.7, 0.9), "min_score": (4.0, 6.0), "temp": (0.7, 1.1),
        "rebalance_range": (0.02, 0.05)
    },
    "technical_swing": {  # Klasyczny swing trader (wykresy średnioterminowe)
        "time_weights": {"short": (0.3, 0.4), "medium": (0.5, 0.6), "long": (0.05, 0.15)},
        "metric_weights": {"tech": (0.5, 0.7), "fund": (0.05, 0.1), "val": (0.05, 0.1), "risk": (0.1, 0.2), "conv": (0.05, 0.1), "asym": (0.05, 0.1)},
        "risk_tolerance": (0.6, 0.8), "min_score": (3.5, 5.0), "temp": (0.8, 1.0),
        "rebalance_range": (0.015, 0.035)
    },
    "macro_fundamentalist": {  # Patrzy na fundamenty i długi termin, ignoruje szum
        "time_weights": {"short": (0.0, 0.05), "medium": (0.2, 0.3), "long": (0.65, 0.8)},
        "metric_weights": {"tech": (0.0, 0.05), "fund": (0.5, 0.7), "val": (0.1, 0.2), "risk": (0.1, 0.2), "conv": (0.05, 0.1), "asym": (0.0, 0.05)},
        "risk_tolerance": (0.3, 0.5), "min_score": (5.5, 7.0), "temp": (1.2, 1.5),
        "rebalance_range": (0.07, 0.15)
    }
}