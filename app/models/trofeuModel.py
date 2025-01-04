from sqlalchemy import Column, Integer, String
from config import Base

class Trofeu(Base):
    __tablename__ = "trofeus"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    descricao = Column(String, nullable=False)
    tag = Column(String, nullable=False)
    imagem = Column(String, nullable=True)