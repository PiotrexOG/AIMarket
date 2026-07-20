from pydantic import BaseModel
from typing import Tuple


class ArchetypeRead(BaseModel):
    key: str
    name: str
    summary: str
    top_m_share: Tuple[float, float]
