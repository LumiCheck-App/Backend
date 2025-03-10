from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from config import Base
from sqlalchemy.sql import func

class ScreenTime(Base):
    __tablename__ = "screentime"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_user = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    usage_data = Column(JSONB, nullable=False)

    user = relationship("User", back_populates="screentimes")  # Aqui, usar "User" como string
