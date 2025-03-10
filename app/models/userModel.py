from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from config import Base

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    onboarding = Column(Boolean, default=False) 

    screentimes = relationship("ScreenTime", back_populates="user", cascade="all, delete-orphan")