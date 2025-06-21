from sqlalchemy import Column, Integer, Boolean, ForeignKey, DateTime
from config import Base

class UserTaskStatus(Base):
    __tablename__ = "task_status"
    id_user = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    id_task = Column(Integer, ForeignKey("task.id", ondelete="CASCADE"))
    done = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    id = Column(Integer, primary_key=True, index=True)