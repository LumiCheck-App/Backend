from sqlalchemy import Column, Integer, Boolean, ForeignKey
from config import Base

class UserTarefaStatus(Base):
    __tablename__ = "users_tarefas_status"
    id_user = Column(Integer, ForeignKey("users.id"), primary_key=True)
    id_tarefa = Column(Integer, ForeignKey("tarefas.id"), primary_key=True)
    done = Column(Boolean, default=False)