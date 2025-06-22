from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from models.userModel import User
from utils import hash_password, verify_password
from auth import create_access_token, get_current_user, create_refresh_token
from config import get_db
from pydantic import BaseModel
from jose import jwt, JWTError
from fastapi import status
from auth import SECRET_KEY, ALGORITHM
from cronjob import assign_missing_tasks

router = APIRouter()

class UserUpdate(BaseModel):
    username: str = None
    email: str = None
    password: str = None
    onboarding: bool = None
    firebase_token: str = None
    is_monitoring: bool = None

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
    # Verifica se o email já existe
    existing_email = db.query(User).filter(
        (User.email == user_data.email)
    ).first()

    existing_username = db.query(User).filter(
        (User.username == user_data.username)
    ).first()
    
    if existing_email:
        raise HTTPException(status_code=400, detail="Este email já está em registado")
    if existing_username:
        raise HTTPException(status_code=400, detail="Este username já está em registado")

    hashed_password = hash_password(user_data.password)

    # Cria o novo usuário
    user = User(
        username=user_data.username,
        email=user_data.email,
        password=hashed_password,
        onboarding=user_data.onboarding,
        )
    
    db.add(user)
    db.commit()
    db.refresh(user)

    assign_missing_tasks()

    return {"message": "User registered successfully", "user_id": user.id}

@router.post("/login")
def login(requestUser: RequestUser, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == requestUser.username).first()
    if not user or not verify_password(requestUser.password, user.password):
        raise HTTPException(status_code=400, detail="Username ou password incorretos")

    user_id = str(user.id)
    access_token = create_access_token(data={"sub": user_id})
    refresh_token = create_refresh_token(data={"sub": user_id})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/refresh")
async def refresh_token(request: Request):
    try:
        body = await request.json()
        refresh_token = body.get("refresh_token")
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

        new_access_token = create_access_token(data={"sub": user_id})
        return {"access_token": new_access_token}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido")


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
    if user_update.firebase_token:
        user.firebase_token = user_update.firebase_token
    if user_update.is_monitoring is not None:
        user.is_monitoring = user_update.is_monitoring

    db.commit()
    db.refresh(user)

    return {"message": f"User with ID {user_id} has been updated", "user": user}
