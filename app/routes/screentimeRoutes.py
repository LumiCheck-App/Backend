from fastapi import APIRouter, HTTPException, Depends, JSONResponse
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

@router.get("/last-7-entries/{user_id}")
def get_last_7_days_by_entries(user_id: int, db: Session = Depends(get_db)):
    # Subquery para pegar os últimos 7 dias distintos registrados no banco para o user
    subquery = (
        db.query(
            func.date(ScreenTime.timestamp).label("day")
        )
        .filter(ScreenTime.id_user == user_id)
        .distinct()
        .order_by(func.date(ScreenTime.timestamp).desc())
        .limit(7)
        .subquery()
    )

    # Consulta principal: pega os registros que estão nesses dias
    entries = (
        db.query(ScreenTime)
        .filter(
            ScreenTime.id_user == user_id,
            func.date(ScreenTime.timestamp).in_(db.query(subquery.c.day))
        )
        .order_by(ScreenTime.timestamp)
        .all()
    )

    if not entries:
        raise HTTPException(status_code=404, detail="No screen time data found for this user")

    # Agrupa os dados por dia no formato dd/mm
    grouped_data = defaultdict(list)
    for entry in entries:
        date_key = entry.timestamp.strftime("%d/%m")
        grouped_data[date_key].append(entry.usage_data)

    # Ordena por data decrescente (últimos dias registrados primeiro)
    sorted_data = dict(sorted(grouped_data.items(), key=lambda x: datetime.strptime(x[0], "%d/%m"), reverse=True))

    return JSONResponse(content=sorted_data)