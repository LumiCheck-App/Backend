from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Boolean
from config import Base

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    onboarding = Column(Boolean, default=False)

    screentimes = relationship("ScreenTime", back_populates="user")  # Aqui, usar "ScreenTime" como string
    digital_habits = relationship("UserDigitalHabitStatus", back_populates="user")