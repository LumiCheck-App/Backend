from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from models.screentimeModel import ScreenTime
from datetime import datetime, timedelta
from collections import defaultdict
from config import get_db
from pydantic import BaseModel
from typing import Dict
from models.achievementModel import UserAchievementStatus, Achievement
from config import sio

router = APIRouter()

from auth import get_current_user
from models.userModel import User

class ScreenTimeCreate(BaseModel):
    id_user: int
    usage_data: Dict 

def check_detox_status(usage_data: Dict) -> bool:
    restricted_keywords = [
        # Social media
        "instagram", "facebook", "messenger", "twitter", "x", "snapchat", "tiktok", 
        # Games
        "clash", "minecraft", "fortnite", "brawl", "candy"
        # Shopping
        "amazon", "ebay", "aliexpress", "nike", "adidas", "shein", "temu", 
        # Gambling/Casinos
        "bet", "casino", "poker"
    ]
    
    app_breakdown = usage_data.get("app_breakdown", {})
    
    for app_name, minutes in app_breakdown.items():
        lower_app = app_name.lower()
    
        if any(keyword in lower_app for keyword in restricted_keywords):
            if minutes > 10:
                return False
    return True

def lumicheck_7_days(db: Session, user_id: int, current_usage: Dict) -> bool:
    # Verifica se usou lumicheck hoje
    app_breakdown = current_usage.get("app_breakdown", {})
    used_today = any("lumicheck" in app.lower() for app in app_breakdown.keys())
    
    if not used_today:
        return False
    
    # Verifica os últimos 6 dias
    today = datetime.now().date()
    for day_offset in range(1, 7): 
        target_date = today - timedelta(days=day_offset)
    
        day_usage = db.query(ScreenTime).filter(
            ScreenTime.id_user == user_id,
            func.date(ScreenTime.timestamp) == target_date
        ).first()
        
        if not day_usage:
            return False
            
        day_apps = day_usage.usage_data.get("app_breakdown", {})
        used_on_day = any("lumicheck" in app.lower() for app in day_apps.keys())
        
        if not used_on_day:
            return False
    
    return True

def less_than_4_hours(usage_data: Dict) -> bool:
    total_minutes = usage_data.get("total_minutes", 0)
    return total_minutes < 240

@router.post("/")
async def create_screentime(entry: ScreenTimeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Check if the user exists
    user = db.query(User).filter(User.id == entry.id_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create a new ScreenTime entry
    new_entry = ScreenTime(
        id_user=entry.id_user,
        usage_data=entry.usage_data,
        timestamp=func.now()
    )
    db.add(new_entry)

    user_id = user.id

    # Verifica se já tem o troféu
    existing_achievement = db.query(UserAchievementStatus).join(Achievement).filter(
        UserAchievementStatus.id_user == user_id,
        Achievement.tag == 'diadedetox'
    ).first()   

    # Se o utilizador completar os requisitos e não tiver o troféu, atribui-o
    if not existing_achievement and check_detox_status(entry.usage_data):
        achievement = db.query(Achievement).filter_by(tag='diadedetox').first()
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

    # Verifica se já tem o troféu
    existing_achievement = db.query(UserAchievementStatus).join(Achievement).filter(
        UserAchievementStatus.id_user == user_id,
        Achievement.tag == 'autoconsciente'
    ).first()   

    # Se o utilizador completar os requisitos e não tiver o troféu, atribui-o
    if not existing_achievement and lumicheck_7_days(db, user_id, entry.usage_data):
        achievement = db.query(Achievement).filter_by(tag='autoconsciente').first()
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

    # Verifica se já tem o troféu
    existing_achievement = db.query(UserAchievementStatus).join(Achievement).filter(
        UserAchievementStatus.id_user == user_id,
        Achievement.tag == 'horaderecolher'
    ).first()   

    # Se o utilizador completar os requisitos e não tiver o troféu, atribui-o
    if not existing_achievement and less_than_4_hours(entry.usage_data):
        achievement = db.query(Achievement).filter_by(tag='horaderecolher').first()
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
    db.refresh(new_entry)

    return {"message": "Screen time entry created successfully", "entry": new_entry}

@router.get("/")
def list_screentime_entries(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(ScreenTime).all()

@router.get("/{user_id}")
def get_user_screentime(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    screentime_entries = db.query(ScreenTime).filter(ScreenTime.id_user == user_id).all()
    if not screentime_entries:
        raise HTTPException(status_code=404, detail="No screen time data found for this user")
    
    return screentime_entries

@router.delete("/{entry_id}")
def delete_screentime_entry(entry_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    entry = db.query(ScreenTime).filter(ScreenTime.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Screen time entry not found")
    
    db.delete(entry)
    db.commit()
    return {"message": f"Screen time entry with ID {entry_id} has been deleted"}

@router.get("/last7days/{user_id}")
def get_last_7days_screentime(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Verificar se o usuário existe
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Calcular a data de 7 dias atrás a partir de agora
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    # Consultar os registros dos últimos 7 dias para o usuário
    entries = db.query(ScreenTime).filter(
        ScreenTime.id_user == user_id,
        ScreenTime.timestamp >= seven_days_ago
    ).order_by(ScreenTime.timestamp).all()

    if not entries:
        raise HTTPException(status_code=404, detail="No screen time data found for this user in the last 7 days")

    # Formatando a resposta com data no formato dd/mm e os dados de uso
    result = []
    for entry in entries:
        # Converter o timestamp para o formato dd/mm
        date_str = entry.timestamp.strftime("%d/%m")
        
        # Extrair o total_minutes do usage_data
        total_minutes = entry.usage_data.get('total_minutes')
        
        # Se não existir total_minutes, pode definir um valor padrão ou pular
        if total_minutes is not None:
            result.append({
                "date": date_str,
                "total_minutes": total_minutes
            })

    return result