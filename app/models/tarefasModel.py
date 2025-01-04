from sqlalchemy import Column, Integer, String
from app.config import Base

class Tarefa(Base):
    __tablename__ = "tarefas"
    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String, nullable=False)