from dataclasses import dataclass, field
from enum import Enum

class State(str, Enum):
    START = "START"
    REGION = "REGION"
    OPF = "OPF"
    OKWED = "OKWED"
    EMPLOYEES = "EMPLOYEES"
    RESULT = "RESULT"

@dataclass
class Reply:
    text: str
    buttons: list[tuple[str, str]] = field(default_factory=list)