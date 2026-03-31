from app.dto.simulation_dto import SimulationDetail
from app.config import START_TIME, END_TIME


class ConfigService:

    @staticmethod
    def get_start_end_dates() -> SimulationDetail:
        return SimulationDetail(
            start_date=START_TIME,
            end_date=END_TIME
        )
