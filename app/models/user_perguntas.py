from sqlalchemy import Column, Integer, ForeignKey
from app.config import Base

class UserPerguntaStatus(Base):
    __tablename__ = "users_perguntas_status"
    id_user = Column(Integer, ForeignKey("users.id"), primary_key=True)
    id_pergunta = Column(Integer, ForeignKey("perguntas.id"), primary_key=True)
    resposta = Column(Integer, nullable=False) 