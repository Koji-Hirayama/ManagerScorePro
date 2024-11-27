from dataclasses import dataclass
from datetime import date, datetime
from typing import List
from sqlalchemy import Column, Integer, String, Float, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

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

class AIModelConfig(Base):
    __tablename__ = 'ai_model_config'

    id = Column(Integer, primary_key=True)
    model_name = Column(String, default='gpt-4')
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2000)

class CacheConfig(Base):
    __tablename__ = 'cache_config'

    id = Column(Integer, primary_key=True)
    enabled = Column(Boolean, default=True)
    ttl_minutes = Column(Integer, default=60)
    max_size_mb = Column(Integer, default=100)
