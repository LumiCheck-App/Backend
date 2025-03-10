from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from config import Base

class DigitalHabit(Base):
    __tablename__ = "digital_habit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)

    users = relationship("UserDigitalHabitStatus", back_populates="habit")  # Usa string em vez de importação direta
