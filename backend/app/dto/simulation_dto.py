from datetime import datetime

from pydantic import BaseModel

class SimulationDetail(BaseModel):
    start_date: datetime
    end_date: datetime
