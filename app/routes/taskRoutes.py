from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models.taskModel import Task
from models.taskStatusModel import UserTaskStatus
from models.achievementModel import Achievement
from models.achievementStatusModel import UserAchievementStatus
from config import get_db
from pydantic import BaseModel
from datetime import date, datetime, time, timedelta
from sqlalchemy import and_, func
from socketio import AsyncServer
from sockets_events import sio

router = APIRouter()

from auth import get_current_user
from models.userModel import User

class TaskCreate(BaseModel):
    description: str

# Cria uma nova tarefa
@router.post("/create")
def create_task(task: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Cria uma nova tarefa no sistema.

    Corpo da requisição (JSON):
    - `description`: Texto descritivo da tarefa a ser adicionada
    """
    new_task = Task(description=task.description)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return {"message": "Task successfully created", "task": new_task}

# Apaga uma tarefa
@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Apaga uma tarefa com base no seu ID.

    Parâmetro:
    - `task_id`: ID da tarefa a remover

    A tarefa será removida permanentemente. Retorna erro 404 se a tarefa não existir.
    """
    task = db.query(Task).filter_by(id=task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return {"message": f"Task with ID {task_id} was successfully deleted"}

# Lista todas as tarefas
@router.get("/")
def list_tasks(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Lista todas as tarefas existentes na app.
    """
    return db.query(Task).all()

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

@router.post("/{task_id}/{user_id}/toggle")
async def toggle_task_completion(task_id: int, user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Altera o estado de conclusão de uma tarefa diária de um utilizador.

    Parâmetros:
    - `task_id`: ID da tarefa
    - `user_id`: ID do utilizador

    Além de atualizar o estado da tarefa, este endpoint também verifica e atribui os seguintes troféus:
    - `marcodos20`: 20 tarefas concluídas no total
    - `dedicado`: 7 dias consecutivos com pelo menos uma tarefa concluída
    - `perfecionista`: 14 dias consecutivos com tarefas concluídas
    - `modozen`: 30 dias consecutivos com tarefas concluídas
    """
    task = db.query(Task).filter_by(id=task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    today = date.today()
    start_of_day = datetime.combine(today, time.min)
    end_of_day = datetime.combine(today, time.max)

    status = db.query(UserTaskStatus).filter(
        UserTaskStatus.id_user == user_id,
        UserTaskStatus.id_task == task_id,
        UserTaskStatus.completed_at >= start_of_day,
        UserTaskStatus.completed_at <= end_of_day
    ).first()

    if not status:
        raise HTTPException(status_code=400, detail="Task is not assigned for today")

    status.done = not status.done
    status.completed_at = datetime.now()

    # Verifica se já tem o troféu "marcodos20"
    existing_achievement = db.query(UserAchievementStatus).join(Achievement).filter(
        UserAchievementStatus.id_user == user_id,
        Achievement.tag == 'marcodos20'
    ).first()

    # Se o utilizador completar 20 tarefas e não tiver o troféu, atribui-o
    if not existing_achievement:
        # Recontar tarefas completas
        completed_tasks_count = db.query(UserTaskStatus).filter(
            UserTaskStatus.id_user == user_id,
            UserTaskStatus.done == True
        ).count()
        if completed_tasks_count >= 20:
            achievement = db.query(Achievement).filter_by(tag='marcodos20').first()
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
    existing_achievement2 = db.query(UserAchievementStatus).join(Achievement).filter(
        UserAchievementStatus.id_user == user_id,
        Achievement.tag == 'dedicado'
    ).first()

    # Se o utilizador completar os requisitos e não tiver o troféu, atribui-o
    if not existing_achievement2 :
        # Ver streak de tarefas concluídas
        streak_tasks_count = get_streak_count(db, user_id)
        if streak_tasks_count >= 7:
            achievement = db.query(Achievement).filter_by(tag='dedicado').first()
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
    existing_achievement3 = db.query(UserAchievementStatus).join(Achievement).filter(
        UserAchievementStatus.id_user == user_id,
        Achievement.tag == 'perfecionista'
    ).first()

    # Se o utilizador completar os requisitos e não tiver o troféu, atribui-o
    if not existing_achievement3 :
        # Ver streak de tarefas concluídas
        streak_tasks_count = get_streak_count(db, user_id)
        if streak_tasks_count >= 14:
            achievement = db.query(Achievement).filter_by(tag='perfecionista').first()
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
    existing_achievement4 = db.query(UserAchievementStatus).join(Achievement).filter(
        UserAchievementStatus.id_user == user_id,
        Achievement.tag == 'modozen'
    ).first()

    # Se o utilizador completar os requisitos e não tiver o troféu, atribui-o
    if not existing_achievement4 :
        # Ver streak de tarefas concluídas
        streak_tasks_count = get_streak_count(db, user_id)
        if streak_tasks_count >= 30:
            achievement = db.query(Achievement).filter_by(tag='modozen').first()
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
    return {"message": f"Task toggled to {status.done}"}

# Mostra as tarefas concluidas por um utilizador (excluindo as do dia atual)
@router.get("/{user_id}/completed")
def list_completed_tasks(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Lista todas as tarefas concluídas por um utilizador, excluindo as realizadas no dia.

    Parâmetro:
    - `user_id`: ID do utilizador

    Retorna uma lista com as tarefas finalizadas antes de hoje, incluindo a data de conclusão.
    """
    today = date.today()
    start_of_day = datetime.combine(today, time.min)
    
    completed_tasks = (
        db.query(Task, UserTaskStatus)
        .join(UserTaskStatus, UserTaskStatus.id_task == Task.id)
        .filter(
            UserTaskStatus.id_user == user_id,
            UserTaskStatus.done == True,
            UserTaskStatus.completed_at < start_of_day  # Só mostra concluídas antes de hoje
        )
        .all()
    )
    
    return [
        {
            "id": task.id, 
            "description": task.description, 
            "completed_at": status.completed_at
        }
        for task, status in completed_tasks
    ]

# Mostra as tarefas diárias (de hoje) atribuídas a um utilizador
@router.get("/{user_id}/dailystatus")
def list_today_tasks_with_status(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Lista todas as tarefas atribuídas ao utilizador no dia atual, incluindo o seu estado.

    Parâmetro:
    - `user_id`: ID do utilizador

    A resposta contém:
    - `id`: ID da tarefa
    - `description`: Texto da tarefa
    - `done`: Booleano indicando se foi concluída
    """
    today = date.today()
    start_of_day = datetime.combine(today, time.min)
    end_of_day = datetime.combine(today, time.max)

    tasks = (
        db.query(
            Task.id,
            Task.description,
            UserTaskStatus.done
        )
        .join(UserTaskStatus, and_(
            UserTaskStatus.id_task == Task.id,
            UserTaskStatus.id_user == user_id,
            UserTaskStatus.completed_at >= start_of_day,
            UserTaskStatus.completed_at <= end_of_day
        ))
        .all()
    )

    return [
        {
            "id": task.id,
            "description": task.description,
            "done": task.done if task.done is not None else False,
        }
        for task in tasks
    ]

# Mostra as tarefas não concluídas de um utilizador
@router.get("/{user_id}/not_completed")
def list_not_completed_tasks(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Lista todas as tarefas atribuídas a um utilizador que ainda não foram concluídas.

    Parâmetro:
    - `user_id`: ID do utilizador
    """
    tasks = (
        db.query(
            Task.id,
            Task.description
        )
        .outerjoin(UserTaskStatus, (UserTaskStatus.id_task == Task.id) & (UserTaskStatus.id_user == user_id))
        .filter((UserTaskStatus.done == False) | (UserTaskStatus.done == None))
        .all()
    )
    return [
        {"id": task.id, "description": task.description}
        for task in tasks
    ]
