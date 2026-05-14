from datetime import datetime

from pydantic import BaseModel

class SimulationDetail(BaseModel):
    start_date: datetime
    end_date: datetime

class ArchetypeDetail(BaseModel):
    archetypes_config: str

class SimulationRequest(BaseModel):
    start_time: datetime | None = None
    end_time: datetime | None = None
    users_per_archetype: int | None = 1
    delta_days: int | None = 7
    archetypes_config: str
    is_batch: bool