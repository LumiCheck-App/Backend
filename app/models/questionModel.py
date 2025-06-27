from sqlalchemy import Column, Integer, String
from config import Base

class Question(Base):
    __tablename__ = "question"
    id = Column(Integer, primary_key=True, index=True)
    question = Column(String, nullable=False)