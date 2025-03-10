from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from config import Base

class UserDigitalHabitStatus(Base):
    __tablename__ = "user_digital_habit"
    id_user = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)
    id_digital_habit = Column(Integer, ForeignKey("digital_habit.id", ondelete="CASCADE"), primary_key=True)

    digital_habit = relationship("DigitalHabit", back_populates="users")