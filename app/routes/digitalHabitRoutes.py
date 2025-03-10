from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.userModel import User
from app.models.digitalHabitModel import DigitalHabit
from app.models.userDigitalHabitModel import UserDigitalHabitStatus
from config import get_db

router = APIRouter()

# Cria um novo hábito digital
@router.post("/create")
def create_digital_habit(name: str, db: Session = Depends(get_db)):
    new_habit = DigitalHabit(name=name)
    db.add(new_habit)
    db.commit()
    db.refresh(new_habit)
    return {"message": "Digital habit successfully created", "digital_habit": new_habit}

# Lista todos os hábitos digitais
@router.get("/")
def list_digital_habits(db: Session = Depends(get_db)):
    return db.query(DigitalHabit).all()

# Associa um hábito digital a um utilizador
@router.post("/{user_id}/digital-habits/{habit_id}")
def associate_digital_habit(user_id: int, habit_id: int, db: Session = Depends(get_db)):
    # Verifica se o hábito existe
    habit = db.query(DigitalHabit).filter_by(id=habit_id).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Digital habit not found")

    # Verifica se já está associado
    status = db.query(UserDigitalHabitStatus).filter_by(id_user=user_id, id_digital_habit=habit_id).first()
    if not status:
        status = UserDigitalHabitStatus(id_user=user_id, id_digital_habit=habit_id)
        db.add(status)
        db.commit()
        return {"message": "Digital habit successfully associated with user"}

    return {"message": "Digital habit is already associated with user"}

# Remove a associação de um hábito digital a um utilizador
@router.delete("/{user_id}/digital-habits/{habit_id}")
def remove_digital_habit(user_id: int, habit_id: int, db: Session = Depends(get_db)):
    # Verifica se já está associado
    status = db.query(UserDigitalHabitStatus).filter_by(id_user=user_id, id_digital_habit=habit_id).first()
    if not status:
        raise HTTPException(status_code=404, detail="Association not found")

    db.delete(status)
    db.commit()
    return {"message": "Digital habit successfully removed from user"}

# Lista os hábitos digitais associados a um utilizador
@router.get("/{user_id}/digital-habits")
def list_associated_digital_habits(user_id: int, db: Session = Depends(get_db)):
    habits = (
        db.query(DigitalHabit)
        .join(UserDigitalHabitStatus, UserDigitalHabitStatus.id_digital_habit == DigitalHabit.id)
        .filter(UserDigitalHabitStatus.id_user == user_id)
        .all()
    )
    return [{"id": habit.id, "name": habit.name} for habit in habits]
