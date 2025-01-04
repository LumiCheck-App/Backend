from sqlalchemy import Column, Integer, ForeignKey, Boolean
from app.config import Base

class UserTrofeuStatus(Base):
    __tablename__ = "users_trofeus_status"
    id_user = Column(Integer, ForeignKey("users.id"), primary_key=True)
    id_trofeu = Column(Integer, ForeignKey("trofeus.id"), primary_key=True)
    done = Column(Boolean, default=False) 