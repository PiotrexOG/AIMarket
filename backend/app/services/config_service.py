from datetime import timedelta, datetime, timezone
from app.dto.simulation_dto import SimulationDetail, ArchetypeDetail


class ConfigService:
    _start_date: datetime = datetime(2025, 3, 19, 13, 30, tzinfo=timezone.utc)
    _end_date: datetime = datetime(2026, 8, 19, 20, 30, tzinfo=timezone.utc)
    _archetype_config = "archetypes_normalized.json"


    @classmethod
    def get_start_end_dates(cls) -> SimulationDetail:
        return SimulationDetail(
            start_date=cls._start_date,
            end_date=cls._end_date
        )

    @classmethod
    def set_start_end_dates(cls, start_date: datetime, end_date: datetime) -> None:
        if start_date >= end_date:
            raise ValueError("start_date musi być wcześniejsza niż end_date")

        cls._start_date = start_date
        cls._end_date = end_date

    @classmethod
    def get_archetype_config(cls) -> ArchetypeDetail:
        return ArchetypeDetail(
            archetypes_config=cls._archetype_config
        )

    @classmethod
    def set_archetype_config(cls, archetype_config: str) -> None:
        cls._archetype_config = archetype_config