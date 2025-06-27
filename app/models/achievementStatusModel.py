from sqlalchemy import Column, Integer, ForeignKey, Boolean
from config import Base

class UserAchievementStatus(Base):
    __tablename__ = "achievement_status"
    id_user = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)
    id_achievement = Column(Integer, ForeignKey("achievement.id", ondelete="CASCADE"), primary_key=True)
    done = Column(Boolean, default=False) 