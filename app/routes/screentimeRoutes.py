from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from models.screentimeModel import ScreenTime
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

