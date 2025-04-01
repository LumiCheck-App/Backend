from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models.userModel import User
from utils import hash_password, verify_password
from auth import create_access_token, get_current_user
from config import get_db
from pydantic import BaseModel

router = APIRouter()

class UserUpdate(BaseModel):
    username: str = None
    email: str = None
    password: str = None
    onboarding: bool = None

class RequestUser(BaseModel):
    username: str
    password: str

class RegisterUser(BaseModel):
    username: str
    email: str
    password: str
    onboarding: bool = False

@router.post("/register")
def register(
    user_data: RegisterUser,  # Agora espera um JSON
    db: Session = Depends(get_db)
):
    # Verifica se o usuário já existe
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    hashed_password = hash_password(user_data.password)

    # Cria o novo usuário
    user = User(
        username=user_data.username,
        email=user_data.email,
        password=hashed_password,
        onboarding=user_data.onboarding
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "User registered successfully", "user_id": user.id}

@router.post("/login")
def login(requestUser: RequestUser, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == requestUser.username).first()
    if not user or not verify_password(requestUser.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "user": user}

@router.get("/")
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@router.delete("/{user_id}") 
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": f"User with ID {user_id} has been deleted"}

@router.get("/protected")
def protected_route(current_user: str = Depends(get_current_user)):
    return {"message": f"Hello, {current_user}!"}

@router.put("/{user_id}")
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update only provided fields
    if user_update.username:
        user.username = user_update.username
    if user_update.email:
        user.email = user_update.email
    if user_update.password:
        user.password = hash_password(user_update.password)
    if user_update.onboarding is not None:
        user.onboarding = user_update.onboarding

    db.commit()
    db.refresh(user)

    return {"message": f"User with ID {user_id} has been updated", "user": user}
