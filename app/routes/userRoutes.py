from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models.userModel import User
from utils import hash_password
from utils import verify_password
from auth import create_access_token, get_current_user
from config import get_db
from pydantic import BaseModel

router = APIRouter()

@router.get("/")
def home():
    return {"message": "Backend iniciado com FastAPI e PostgreSQL"}

@router.post("/register")
def register(
    username: str,
    email: str,
    password: str,
    type: str,  # Tipo do utilizador (deve ser "direct" ou "surrogate")
    idade: int, 
    onboarding: bool = False, 
    db: Session = Depends(get_db)
):
    # Validar o campo 'type'
    if type not in ["direct", "surrogate"]:
        raise HTTPException(status_code=400, detail="Invalid type. Must be 'direct' or 'surrogate'.")

    # Verificar se o email ou username já existem
    existing_user = db.query(User).filter((User.email == email) | (User.username == username)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    hashed_password = hash_password(password)

    # Criar um novo utilizador
    user = User(
        username=username,
        email=email,
        password=hashed_password,
        type=type,
        idade=idade,
        onboarding=onboarding
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "User registered successfully", "user_id": user.id}

@router.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users") #Lista todos os users
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@router.delete("/users/{user_id}") #Apaga o utilizador pelo seu id
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

class UserUpdate(BaseModel):
    username: str = None
    email: str = None
    password: str = None
    type: str = None
    idade: int = None
    onboarding: bool = None

@router.put("/users/{user_id}") #Edita o user pelo id. Caso não queiramos alterar algo, basta colocar igual
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Atualiza apenas os campos fornecidos
    if user_update.username:
        user.username = user_update.username
    if user_update.email:
        user.email = user_update.email
    if user_update.password:
        user.password = hash_password(user_update.password) 
    if user_update.type:
        if user_update.type not in ["direct", "surrogate"]:
            raise HTTPException(status_code=400, detail="Invalid type. Must be 'direct' or 'surrogate'.")
        user.type = user_update.type
    if user_update.idade:
        user.idade = user_update.idade
    if user_update.onboarding is not None:
        user.onboarding = user_update.onboarding

    db.commit()
    db.refresh(user)

    return {"message": f"User with ID {user_id} has been updated", "user": user}