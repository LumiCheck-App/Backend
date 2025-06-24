from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models.userModel import User
from models.taskModel import Task
from models.digitalHabitModel import DigitalHabit
from models.taskStatusModel import UserTaskStatus
from models.userDigitalHabitModel import UserDigitalHabitStatus
from models.achievementModel import Achievement
from models.achievementStatusModel import UserAchievementStatus
from config import get_db
from pydantic import BaseModel
from typing import Optional
from socketio import AsyncServer
from sockets_events import sio

router = APIRouter()

class AchievementCreate(BaseModel):
    name: str
    description: str
    tag: str
    image: Optional[str] = None

# Lista os trofeus
@router.get("/")
def list_achievements(db: Session = Depends(get_db)):
    return db.query(Achievement).all()

# Cria um novo trofeu
@router.post("/create")
def create_achievement(achievement_data: AchievementCreate, db: Session = Depends(get_db)):
    new_achievement = Achievement(name=achievement_data.name, description=achievement_data.description, tag=achievement_data.tag, image=achievement_data.image)
    db.add(new_achievement)
    db.commit()
    db.refresh(new_achievement)
    return {"message": "Achievement successfully created", "achievement": new_achievement}

# Atualiza um trofeu
@router.put("/{achievement_id}")
def update_achievement(achievement_id: int, name: str = None, description: str = None, tag: str = None, image: str = None, db: Session = Depends(get_db)):
    achievement = db.query(Achievement).filter_by(id=achievement_id).first()
    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")

    if name:
        achievement.name = name
    if description:
        achievement.description = description
    if tag:
        achievement.tag = tag
    if image:
        achievement.image = image

    db.commit()
    db.refresh(achievement)
    return {"message": "Achievement successfully updated", "achievement": achievement}

# Apaga um trofeu
@router.delete("/{achievement_id}")
def delete_achievement(achievement_id: int, db: Session = Depends(get_db)):
    achievement = db.query(Achievement).filter_by(id=achievement_id).first()
    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")

    db.delete(achievement)
    db.commit()
    return {"message": "Achievement successfully deleted"}

# Associa um trofeu a um utilizador
@router.post("/{user_id}/{achievement_id}/unlock")
async def unlock_achievement(user_id: int, achievement_id: int, db: Session = Depends(get_db)):
    #Verifica se o troféu existe
    achievement = db.query(Achievement).filter_by(id=achievement_id).first()
    if not achievement:
        raise HTTPException(status_code=404, detail="Troféu não encontrado")
    
    # Verifica se já tem o troféu
    existing_achievement = db.query(UserAchievementStatus).join(Achievement).filter(
        UserAchievementStatus.id_user == user_id,
        Achievement.id == achievement_id
    ).first()

    # 3. Atualiza ou cria o registro do troféu
    if not existing_achievement:
        user_achievement = UserAchievementStatus(
            id_user=user_id,
            id_achievement=achievement_id,
            done=True,
            # achieved_at=datetime.now() 
        )
        db.add(user_achievement)
        await sio.emit(
            'trophy_unlocked',
            {
                "title": achievement.name,
                "description": achievement.description
            },
            room=f"user_{user_id}"
        )

    db.commit()
    return {"message": "Achievement marked as unlocked"}

#Lista os trofeus desbloqueados por um utilizador
@router.get("/{user_id}/unlocked")
def list_unlocked_achievements(user_id: int, db: Session = Depends(get_db)):
    achievements = (
        db.query(Achievement)
        .join(UserAchievementStatus, UserAchievementStatus.id_achievement == Achievement.id)
        .filter(UserAchievementStatus.id_user == user_id, UserAchievementStatus.done == True)
        .all()
    )
    return [{"id": achievement.id, "name": achievement.name, "description": achievement.description, "tag": achievement.tag, "image": achievement.image} for achievement in achievements]

# Lista todos os trofeus (conquistados ou não) de um utilizador
@router.get("/{user_id}/status")
def list_achievements_with_status(user_id: int, db: Session = Depends(get_db)):
    achievements = (
        db.query(
            Achievement.id,
            Achievement.name,
            Achievement.description,
            UserAchievementStatus.done
        )
        .outerjoin(UserAchievementStatus, (UserAchievementStatus.id_achievement == Achievement.id) & (UserAchievementStatus.id_user == user_id))
        .all()
    )
    return [
        {"id": achievement.id, "name": achievement.name, "description": achievement.description, "unlocked": True if achievement.done else False}
        for achievement in achievements
    ]
