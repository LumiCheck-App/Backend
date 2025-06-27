from sqlalchemy import Column, Integer, ForeignKey
from config import Base

class UserQuestionAnswer(Base):
    __tablename__ = "question_status"
    id_user = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)
    id_question = Column(Integer, ForeignKey("question.id", ondelete="CASCADE"), primary_key=True)
    answer = Column(Integer, nullable=False) 