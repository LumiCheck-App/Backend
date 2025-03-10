from sqlalchemy import Column, Integer, String
from config import Base

class Achievement(Base):
    __tablename__ = "achievement"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    tag = Column(String, nullable=False)
    image = Column(String, nullable=True)