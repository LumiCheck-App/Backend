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
from datetime import datetime, timedelta
from sqlalchemy import and_, func
from models.taskStatusModel import UserTaskStatus

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

#Lista os trofeus bloqueados de um utilizador
@router.get("/{user_id}/locked")
def list_unlocked_achievements(user_id: int, db: Session = Depends(get_db)):
    unlocked_achievements = (
        db.query(Achievement)
        .join(UserAchievementStatus, UserAchievementStatus.id_achievement == Achievement.id)
        .filter(UserAchievementStatus.id_user == user_id, UserAchievementStatus.done == True)
        .all()
    )

    achievements = (
        db.query(Achievement)
        .filter(Achievement.id.notin_([achievement.id for achievement in unlocked_achievements]))
        .all()
    )
    return [{"id": achievement.id, "name": achievement.name, "description": achievement.description, "tag": achievement.tag, "image": achievement.image} for achievement in achievements]


def get_streak_count(db: Session, user_id: int) -> int:
    # ÚNICA CONSULTA que busca todas as datas com tarefas concluídas
    dates = db.query(
        func.date(UserTaskStatus.completed_at).label('task_date')
    ).filter(
        UserTaskStatus.id_user == user_id,
        UserTaskStatus.done == True
    ).distinct().order_by(
        func.date(UserTaskStatus.completed_at).desc()
    ).all()
    
    if not dates:
        return 0
    
    # Processamento em memória
    dates = [d[0] for d in dates]  # Converte para objetos date
    today = datetime.now().date()
    
    # Se não há tarefa concluída hoje, streak = 0
    if dates[0] != today:
        return 0
    
    streak = 1
    # Verifica dias consecutivos
    for i in range(1, len(dates)):
        if dates[i] == (dates[i-1] - timedelta(days=1)):
            streak += 1
        else:
            break
    
    return streak


# Função auxiliar para obter o número de tarefas concluídas consecutivas
@router.get("/{user_id}/checkModoZen")
def check_modo_zen_progress(user_id: int, db: Session = Depends(get_db)):
    existing_achievement = db.query(UserAchievementStatus).join(Achievement).filter(
        UserAchievementStatus.id_user == user_id,
        Achievement.tag == 'modozen'
    ).first()

    achievement = db.query(Achievement).filter_by(tag='modozen').first()

    if existing_achievement and existing_achievement.done:
        return {
            "unlocked": True,
            "progress": 30,
            "total": 30,
            "achievement": {
                "id": achievement.id,
                "name": achievement.name,
                "description": achievement.description,
                "tag": achievement.tag,
                "image": achievement.image
            }
        }
    else:
        streak_count = get_streak_count(db, user_id)
        return {
            "unlocked": False,
            "progress": streak_count,
            "total": 30,
            "achievement": {
                "id": achievement.id,
                "name": achievement.name,
                "description": achievement.description,
                "tag": achievement.tag,
                "image": achievement.image
            }
        }

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
