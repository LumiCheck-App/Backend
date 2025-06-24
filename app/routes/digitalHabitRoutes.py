from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models.digitalHabitModel import DigitalHabit
from models.userDigitalHabitModel import UserDigitalHabitStatus
from config import get_db
from pydantic import BaseModel
from typing import List

router = APIRouter()

from auth import get_current_user
from models.userModel import User

class DigitalHabitCreate(BaseModel):
    name: str

# Cria um novo hábito digital
@router.post("/create")
def create_digital_habit(body: DigitalHabitCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_habit = DigitalHabit(name=body.name)
    db.add(new_habit)
    db.commit()
    db.refresh(new_habit)
    return {"message": "Digital habit successfully created", "digital_habit": new_habit}

# Lista todos os hábitos digitais
@router.get("/")
def list_digital_habits(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(DigitalHabit).all()

class HabitsAssociationRequest(BaseModel):
    habit_ids: List[int]

@router.post("/{user_id}")
def associate_digital_habits(user_id: int, body: HabitsAssociationRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    associated = 0

    for habit_id in body.habit_ids:
        # Verifica se o hábito existe
        habit = db.query(DigitalHabit).filter_by(id=habit_id).first()
        if not habit:
            continue  # ignora IDs inválidos

        # Verifica se já está associado
        status = db.query(UserDigitalHabitStatus).filter_by(id_user=user_id, id_digital_habit=habit_id).first()
        if not status:
            status = UserDigitalHabitStatus(id_user=user_id, id_digital_habit=habit_id)
            db.add(status)
            associated += 1

    db.commit()
    return {"message": f"{associated} hábito(s) associados com sucesso ao utilizador {user_id}"}

# Remove a associação de um hábito digital a um utilizador
@router.delete("/{user_id}/{habit_id}")
def remove_digital_habit(user_id: int, habit_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Verifica se já está associado
    status = db.query(UserDigitalHabitStatus).filter_by(id_user=user_id, id_digital_habit=habit_id).first()
    if not status:
        raise HTTPException(status_code=404, detail="Association not found")

    db.delete(status)
    db.commit()
    return {"message": "Digital habit successfully removed from user"}

# Lista os hábitos digitais associados a um utilizador
@router.get("/{user_id}")
def list_associated_digital_habits(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    habits = (
        db.query(DigitalHabit)
        .join(UserDigitalHabitStatus, UserDigitalHabitStatus.id_digital_habit == DigitalHabit.id)
        .filter(UserDigitalHabitStatus.id_user == user_id)
        .all()
    )
    return [{"id": habit.id, "name": habit.name} for habit in habits]
