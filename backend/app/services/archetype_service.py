from typing import List

from sqlalchemy.orm import Session

from app.config.archetype_config import get_archetype


class ArchetypeService:
    def __init__(self, archetype_config: str):
        self.archetype_config = archetype_config
        self.raw_data = get_archetype(self.archetype_config)

    # Mapujemy komentarze na dane


    DESCRIPTIONS = {
        "benchmark": "Kup po równo i trzymaj",
        "conservative_grandpa": "Skrajnie bezpieczny, tylko long-term",
        "value_hunter": "Szuka niedoszacowanych perełek",
        "degen_trader": "Agresywny, techniczny, krótkoterminowy",
        "growth_enthusiast": "Stawia na momentum i przyszłość",
        "risk_manager": "Priorytetem jest ochrona kapitału (structural risk)",
        "balanced_pensioner": "Klasyczne 60/40, umiarkowany spokój",
        "conviction_heavy": "Gra tylko pod to, w co mocno wierzy",
        "asymmetry_seeker": "Szuka układów o małym ryzyku i wielkim potencjale (black swans)",
        "technical_swing": "Klasyczny swing trader (wykresy średnioterminowe)",
        "macro_fundamentalist": "Patrzy na fundamenty i długi termin, ignoruje szum"
    }

    def _format_archetype(self, key: str, data: dict) -> dict:
        """Helper do formatowania pojedynczego archetypu"""
        return {
            "key": key,
            "name": key.replace("_", " ").title(),
            "summary": self.DESCRIPTIONS.get(key, "Brak opisu"),
            **data
        }

    def get_all_archetypes(self) -> List[dict]:
        """Zwraca listę wszystkich dostępnych archetypów"""
        return [self._format_archetype(k, v) for k, v in self.raw_data.items()]

    def get_archetype_by_key(self, key: str) -> dict:
        """Zwraca konkretny archetyp po kluczu"""
        data = self.raw_data.get(key)
        if not data:
            return None
        return self._format_archetype(key, data)