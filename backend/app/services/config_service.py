from datetime import timedelta, datetime, timezone
from app.dto.simulation_dto import SimulationDetail


class ConfigService:
    _start_date: datetime = datetime(2025, 3, 19, 13, 30, tzinfo=timezone.utc)
    _end_date: datetime = datetime(2026, 4, 28, 20, 30, tzinfo=timezone.utc)


    @classmethod
    def get_start_end_dates(cls) -> SimulationDetail:
        return SimulationDetail(
            start_date=cls._start_date + timedelta(days=1),
            end_date=cls._end_date
        )

    @classmethod
    def set_start_end_dates(cls, start_date: datetime, end_date: datetime) -> None:
        if start_date >= end_date:
            raise ValueError("start_date musi być wcześniejsza niż end_date")

        cls._start_date = start_date
        cls._end_date = end_date