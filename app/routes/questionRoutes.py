from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models.questionModel import Question
from models.questionStatusModel import UserQuestionAsnwer
from config import get_db
from pydantic import BaseModel

router = APIRouter()

class QuestionCreate(BaseModel):
    question: str

class QuestionAnswer(BaseModel):
    user_id: int
    question_id: int
    answer: int

# Cria uma pergunta
@router.post("/create")
def create_question(body: QuestionCreate, db: Session = Depends(get_db)):
    new_question = Question(question=body.question)
    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    return {"message": "Question successfully created", "question": new_question}

# Lista todas as perguntas
@router.get("/")
def list_questions(db: Session = Depends(get_db)):
    return db.query(Question).all()

# Atribui a resposta de um utilizador a uma pergunta
@router.post("/asnwer")
def add_question_asnwer(body: QuestionAnswer, db: Session = Depends(get_db)):
    if not (0 <= body.answer <= 5):
        raise HTTPException(status_code=400, detail="Answer must be between 0 and 5")
    
    asnwer = UserQuestionAsnwer(id_user=body.user_id, id_question=body.question_id, answer=body.answer)
    db.add(asnwer)
    db.commit()
    return {"message": "Question asnwer successfully added"}

# Atualiza a resposta de um utilizador a uma pergunta
@router.put("/asnwer")
def update_question_asnwer(body: QuestionAnswer, db: Session = Depends(get_db)):
    answer = db.query(UserQuestionAsnwer).filter_by(id_user=body.user_id, id_question=body.question_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="asnwer not found")
    
    if not (0 <= body.answer <= 5):
        raise HTTPException(status_code=400, detail="Answer must be between 0 and 5")
    
    answer.answer = body.answer
    db.commit()
    return {"message": "Question status successfully updated"}

# Lista as respostas de um utilizador
@router.get("/{user_id}/answers")
def list_user_answers(user_id: int, db: Session = Depends(get_db)):
    answers = (
        db.query(UserQuestionAsnwer, Question)
        .join(Question, UserQuestionAsnwer.id_question == Question.id)
        .filter(UserQuestionAsnwer.id_user == user_id)
        .all()
    )
    return [
        {"question_id": question.id, "question": question.question, "answer": answer.answer}
        for answer, question in answers
    ]

# Apaga uma pergunta
@router.delete("/{question_id}")
def delete_question(question_id: int, db: Session = Depends(get_db)):
    question = db.query(Question).filter_by(id=question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    db.delete(question)
    db.commit()
    return {"message": f"Question with ID {question_id} successfully deleted"}
