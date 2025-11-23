from typing import List, Dict
from pydantic import BaseModel

class Slot(BaseModel):
    time: str
    courts: List[str]
    court_ids: List[int]
    is_new: bool

class DayAvailability(BaseModel):
    date: str
    slots: List[Slot]
    new_count: int
    free_slots_map: Dict[str, List[int]]
