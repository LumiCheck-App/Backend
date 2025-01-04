from sqlalchemy import Column, Integer, String
from config import Base

class Pergunta(Base):
    __tablename__ = "perguntas"
    id = Column(Integer, primary_key=True, index=True)
    pergunta = Column(String, nullable=False)