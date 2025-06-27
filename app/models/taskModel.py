from sqlalchemy import Column, Integer, String
from config import Base

class Task(Base):
    __tablename__ = "task"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)