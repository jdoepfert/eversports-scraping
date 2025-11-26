from typing import Dict, List

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


class TargetDate(BaseModel):
    date: str  # ISO format YYYY-MM-DD
    start_time: str | None = None  # HH:MM format, local time
    end_time: str | None = None  # HH:MM format, local time
