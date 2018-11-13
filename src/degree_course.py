from typing import List, Dict
from dataclasses import dataclass


@dataclass
class DegreeCourse:
    name: str
    code: str
    department: str  # 'scuola' in APIs
    years: List[Dict[str, str]]
