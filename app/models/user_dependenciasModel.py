from sqlalchemy import Column, Integer, ForeignKey
from app.config import Base

class UserDependenciaStatus(Base):
    __tablename__ = "users_has_dependencias"
    id_user = Column(Integer, ForeignKey("users.id"), primary_key=True)
    id_dependencia = Column(Integer, ForeignKey("dependencia.id"), primary_key=True)