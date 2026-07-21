from typing import List

from app.portfolio_generation.archetype_config import get_archetype


class ArchetypeService:
    DESCRIPTIONS = {
        "benchmark": "Kupuje 100% dostepnych spolek po rowno.",
        "random": "Losuje udzial Top M, czas inwestycji 100-300 dni i rebalance po 20-60% czasu inwestycji.",
    }

    def __init__(self, archetype_config: str):
        self.archetype_config = archetype_config
        self.raw_data = get_archetype(self.archetype_config)

    def _format_archetype(self, key: str, data: dict) -> dict:
        return {
            "key": key,
            "name": key.replace("_", " ").title(),
            "summary": self.DESCRIPTIONS.get(key, "Brak opisu"),
            **data,
        }

    def get_all_archetypes(self) -> List[dict]:
        return [self._format_archetype(k, v) for k, v in self.raw_data.items()]

    def get_archetype_by_key(self, key: str) -> dict | None:
        data = self.raw_data.get(key)
        if not data:
            return None
        return self._format_archetype(key, data)
