from datetime import datetime
from dataclasses import dataclass


@dataclass
class Lecture:
    course: str
    room: str
    begin: datetime
    end: datetime
    day: int
