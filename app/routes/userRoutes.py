from fastapi import APIRouter, HTTPException, Depends, Request, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models.userModel import User
from models.achievementStatusModel import UserAchievementStatus
from models.questionStatusModel import UserQuestionAnswer
from models.screentimeModel import ScreenTime
from models.taskStatusModel import UserTaskStatus
from models.userDigitalHabitModel import UserDigitalHabitStatus
from utils import hash_password, verify_password
from auth import create_access_token, get_current_user, create_refresh_token
from config import get_db
from pydantic import BaseModel
from jose import jwt, JWTError
from fastapi import status
from auth import SECRET_KEY, ALGORITHM
from cronjob import assign_missing_tasks
import logging
from fastapi.security import OAuth2PasswordRequestForm

logger = logging.getLogger(__name__)
router = APIRouter()

class UserCredentialsUpdate(BaseModel):
    current_password: str
    new_username: str = None
    new_email: str = None

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
    """
    Regista um novo utilizador no sistema.

    Campos do JSON:
    - `username`: Nome de utilizador (único)
    - `email`: Endereço de email (único)
    - `password`: Palavra-passe
    - `onboarding`: (opcional) Flag para estado inicial da onboarding

    Verifica se o `email` e `username` já existem antes de criar o utilizador. Atribui tarefas iniciais automaticamente.
    """
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
    """
    Realiza o login de um utilizador com base no nome de utilizador e palavra-passe.

    Campos esperados:
    - `username`
    - `password`

    Retorna um token de acesso (`access_token`), um token de renovação (`refresh_token`) e os dados do utilizador.
    """
    user = db.query(User).filter(User.username == requestUser.username).first()
    if not user or not verify_password(requestUser.password, user.password):
        raise HTTPException(status_code=401, detail="Username ou password incorretos")

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
    """
    Gera um novo token de acesso a partir de um `refresh_token` válido.

    Corpo da requisição:
    - `refresh_token`: Token de renovação JWT previamente obtido

    Se o token for válido, retorna um novo `access_token`.
    """
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
def list_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Lista todos os utilizadores registados.
    """
    return db.query(User).all()

class DeleteUserRequest(BaseModel):
    password: str

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    delete_request: DeleteUserRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Elimina completamente a conta de um utilizador.

    Parâmetros:
    - `user_id`: ID do utilizador a eliminar

    Corpo da requisição:
    - `password`: Palavra-passe do utilizador (para confirmação)

    Antes de eliminar:
    - Verifica se o utilizador autenticado é o mesmo
    - Remove todos os dados relacionados (tarefas, respostas, hábitos, etc.)
    """
    if int(current_user.id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own account"
        )

    try:
        # Verificar usuário e senha primeiro
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not verify_password(delete_request.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password"
            )

        logger.info(f"Starting deletion process for user {user_id}")
        
        db.query(UserAchievementStatus).filter(UserAchievementStatus.id_user == user_id).delete()
        db.query(UserQuestionAnswer).filter(UserQuestionAnswer.id_user == user_id).delete()
        db.query(ScreenTime).filter(ScreenTime.id_user == user_id).delete()
        db.query(UserTaskStatus).filter(UserTaskStatus.id_user == user_id).delete()
        db.query(UserDigitalHabitStatus).filter(UserDigitalHabitStatus.id_user == user_id).delete()
        
        db.delete(user)
        db.commit() 
        
        logger.info(f"User {user_id} deleted successfully")
        return {"message": f"User with ID {user_id} has been deleted", "success": True}

    except HTTPException:
        raise
        
    except SQLAlchemyError as sae:
        db.rollback()
        logger.error(f"Database error during user deletion: {str(sae)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while deleting user"
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during user deletion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@router.get("/protected")
def protected_route(current_user: User = Depends(get_current_user)):
    """
    Rota protegida para verificar se o token JWT é válido.

    Retorna uma mensagem com o ID do utilizador autenticado.
    """
    return {"message": f"Hello, {current_user.id}!"}

@router.put("/{user_id}")
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Atualiza os dados do perfil de um utilizador.

    Parâmetros:
    - `user_id`: ID do utilizador a atualizar

    Corpo da requisição pode conter:
    - `username`, `email`, `password`, `onboarding`, `firebase_token`, `is_monitoring`
    """
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


@router.put("/{user_id}/updatecredentials")
def update_user_credentials(
    user_id: int,
    credentials_update: UserCredentialsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Atualiza o username ou email do utilizador autenticado, após confirmação da palavra-passe atual.

    Parâmetros:
    - `user_id`: ID do utilizador

    Corpo da requisição:
    - `current_password`: Palavra-passe atual
    - `new_username`: (opcional) Novo username
    - `new_email`: (opcional) Novo email

    Valida se os novos valores já estão em uso antes de atualizar.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verificar senha
    if not verify_password(credentials_update.current_password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )
    
    updated_fields = {}
    
    # Atualizar username se fornecido
    if credentials_update.new_username:
        # Verificar se username já existe
        existing_user = db.query(User).filter(User.username == credentials_update.new_username).first()
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        user.username = credentials_update.new_username
        updated_fields["username"] = credentials_update.new_username
    
    # Atualizar email se fornecido
    if credentials_update.new_email:
        # Verificar se email já existe
        existing_email = db.query(User).filter(User.email == credentials_update.new_email).first()
        if existing_email and existing_email.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        user.email = credentials_update.new_email
        updated_fields["email"] = credentials_update.new_email
    
    db.commit()
    db.refresh(user)
    
    return {
        "success": True,
        "message": "Credentials updated successfully",
        "updated_fields": updated_fields,
        "user": user
    }