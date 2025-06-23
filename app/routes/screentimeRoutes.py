from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from models.screentimeModel import ScreenTime
from datetime import datetime, timedelta
from collections import defaultdict
from models.userModel import User
from config import get_db
from pydantic import BaseModel
from typing import Dict

router = APIRouter()

class ScreenTimeCreate(BaseModel):
    id_user: int
    usage_data: Dict  # JSON format

@router.post("/")
def create_screentime(entry: ScreenTimeCreate, db: Session = Depends(get_db)):
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
    db.commit()
    db.refresh(new_entry)

    return {"message": "Screen time entry created successfully", "entry": new_entry}

@router.get("/")
def list_screentime_entries(db: Session = Depends(get_db)):
    return db.query(ScreenTime).all()

@router.get("/{user_id}")
def get_user_screentime(user_id: int, db: Session = Depends(get_db)):
    screentime_entries = db.query(ScreenTime).filter(ScreenTime.id_user == user_id).all()
    if not screentime_entries:
        raise HTTPException(status_code=404, detail="No screen time data found for this user")
    
    return screentime_entries

@router.delete("/{entry_id}")
def delete_screentime_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(ScreenTime).filter(ScreenTime.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Screen time entry not found")
    
    db.delete(entry)
    db.commit()
    return {"message": f"Screen time entry with ID {entry_id} has been deleted"}

@router.get("/last7days/{user_id}")
def get_last_7days_screentime(user_id: int, db: Session = Depends(get_db)):
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