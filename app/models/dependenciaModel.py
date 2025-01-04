from sqlalchemy import Column, Integer, String
from config import Base

class Dependencia(Base):
    __tablename__ = "dependencia"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False) 