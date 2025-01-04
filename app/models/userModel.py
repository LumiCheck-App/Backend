from sqlalchemy import Column, Integer, String, Boolean
from app.config import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    type = Column(String)
    idade = Column(Integer)
    onboarding = Column(Boolean, default=False) 