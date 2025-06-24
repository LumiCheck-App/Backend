from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
from models.questionModel import Question
from models.questionStatusModel import UserQuestionAnswer
from models.achievementModel import Achievement
from models.achievementStatusModel import UserAchievementStatus
from config import get_db
from pydantic import BaseModel
from typing import List
from socketio import AsyncServer
from sockets_events import sio
import random

from core.security import get_current_user
from models.userModel import User

router = APIRouter()

class QuestionCreate(BaseModel):
    question: str

class QuestionAnswer(BaseModel):
    user_id: int
    question_id: int
    answer: int

# Cria uma pergunta
@router.post("/create")
def create_question(body: QuestionCreate, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    new_question = Question(question=body.question)
    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    return {"message": "Question successfully created", "question": new_question}

# Lista todas as perguntas
@router.get("/")
def list_questions(db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    return db.query(Question).all()

# Atribui a resposta de um utilizador a uma pergunta
@router.post("/answer")
def add_question_answer(
    body: List[QuestionAnswer] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    print("Received answers:", body)
    if not body:
        raise HTTPException(status_code=400, detail="No answers provided")
    question_ids = {ans.question_id for ans in body}
    print("Question IDs:", question_ids)
    for ans in body:
        if not (0 <= ans.answer <= 5):
            raise HTTPException(status_code=400, detail="Answer must be between 0 and 5")
        
        db_answer = UserQuestionAnswer(
            id_user=ans.user_id,
            id_question=ans.question_id,
            answer=ans.answer
        )
        db.add(db_answer)

    db.commit()
    return {"message": f"{len(body)} answer(s) successfully added"}


# Atualiza a resposta de um utilizador a uma pergunta
@router.put("/answer")
async def update_question_answer(body: QuestionAnswer, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    answer = db.query(UserQuestionAnswer).filter_by(id_user=body.user_id, id_question=body.question_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="answer not found")
    
    if not (0 <= body.answer <= 5):
        raise HTTPException(status_code=400, detail="Answer must be between 0 and 5")
    
    answer.answer = body.answer
    user_id = body.user_id

    # Verifica se já tem o troféu
    existing_achievement = db.query(UserAchievementStatus).join(Achievement).filter(
        UserAchievementStatus.id_user == user_id,
        Achievement.tag == 'primeiropasso'
    ).first()

    # Se o utilizador completar os requisitos e não tiver o troféu, atribui-o
    if not existing_achievement:
        achievement = db.query(Achievement).filter_by(tag='primeiropasso').first()
        if achievement:
            user_achievement = UserAchievementStatus(
                id_user=user_id,
                id_achievement=achievement.id,
                done=True,
                #achieved_at=datetime.now()
            )
            db.add(user_achievement)
            await sio.emit(
                'trophy_unlocked',
                {
                    "title": achievement.name,
                    "description": achievement.description,
                    "image": achievement.image
                },
                room=f"user_{user_id}"
            )

    db.commit()
    return {"message": "Question status successfully updated"}

# Lista as respostas de um utilizador
@router.get("/{user_id}/answers")
def list_user_answers(user_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    answers = (
        db.query(UserQuestionAnswer, Question)
        .join(Question, UserQuestionAnswer.id_question == Question.id)
        .filter(UserQuestionAnswer.id_user == user_id)
        .all()
    )
    return [
        {"question_id": question.id, "question": question.question, "answer": answer.answer}
        for answer, question in answers
    ]

# Dá uma pergunta que o utilizador ainda não respondeu
@router.get("/{user_id}/random_unanswered")
def random_unanswered_question(user_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    answered_question_ids = (
        db.query(UserQuestionAnswer.id_question)
        .filter(UserQuestionAnswer.id_user == user_id)
        .all()
    )

    answered_ids = [answer.id_question for answer in answered_question_ids]
    
    # Filtra as perguntas que o utilizador ainda não respondeu
    unanswered_questions = (
        db.query(Question)
        .filter(Question.id.notin_(answered_ids))
        .all()
    )
    if not unanswered_questions:
        raise HTTPException(status_code=404, detail="No unanswered questions found for this user")
    
    # Seleciona uma pergunta aleatória
    question = random.choice(unanswered_questions)

    # Retorna a pergunta não respondida (não as respondidas!)
    return {
        "question_id": question.id, 
        "question": question.question,
        "total_unanswered": len(unanswered_questions)
    }

# Apaga uma pergunta
@router.delete("/{question_id}")
def delete_question(question_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    question = db.query(Question).filter_by(id=question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    db.delete(question)
    db.commit()
    return {"message": f"Question with ID {question_id} successfully deleted"}
