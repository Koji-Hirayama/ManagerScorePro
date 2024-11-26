from dataclasses import dataclass
from datetime import date
from typing import List

@dataclass
class ManagerScore:
    communication: float
    support: float
    goal_management: float
    leadership: float
    problem_solving: float
    strategy: float

    def to_list(self) -> List[float]:
        return [
            self.communication,
            self.support,
            self.goal_management,
            self.leadership,
            self.problem_solving,
            self.strategy
        ]

@dataclass
class Manager:
    id: int
    name: str
    department: str
    scores: ManagerScore
