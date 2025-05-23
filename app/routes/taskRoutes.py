from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models.userModel import User
from models.taskModel import Task
from models.taskStatusModel import UserTaskStatus
from config import get_db
from pydantic import BaseModel
from datetime import date, datetime, time
from sqlalchemy import and_


router = APIRouter()

class TaskCreate(BaseModel):
    description: str

# Cria uma nova tarefa
@router.post("/create")
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    new_task = Task(description=task.description)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return {"message": "Task successfully created", "task": new_task}

# Apaga uma tarefa
@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter_by(id=task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return {"message": f"Task with ID {task_id} was successfully deleted"}

# Lista todas as tarefas
@router.get("/")
def list_tasks(db: Session = Depends(get_db)):
    return db.query(Task).all()

@router.post("/{task_id}/{user_id}/toggle")
def toggle_task_completion(task_id: int, user_id: int, db: Session = Depends(get_db)):
    # Verifica se a tarefa existe
    task = db.query(Task).filter_by(id=task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Define intervalo do dia de hoje
    today = date.today()
    start_of_day = datetime.combine(today, time.min)
    end_of_day = datetime.combine(today, time.max)

    # Verifica se a tarefa está atribuída ao utilizador e é de hoje
    status = db.query(UserTaskStatus).filter(
        UserTaskStatus.id_user == user_id,
        UserTaskStatus.id_task == task_id,
        UserTaskStatus.completed_at >= start_of_day,
        UserTaskStatus.completed_at <= end_of_day
    ).first()

    if not status:
        raise HTTPException(status_code=400, detail="Task is not assigned for today")

    # Atualiza como concluída
    status.done = not status.done
    status.completed_at = datetime.utcnow()

    db.commit()
    return {"message": f"Task toggled to {status.done}"}

# Mostra as tarefas concluidas por um utilizador
@router.get("/{user_id}/completed")
def list_completed_tasks(user_id: int, db: Session = Depends(get_db)):
    completed_tasks = (
        db.query(Task)
        .join(UserTaskStatus, UserTaskStatus.id_task == Task.id)
        .filter(UserTaskStatus.id_user == user_id, UserTaskStatus.done == True)
        .all()
    )
    return [
        {"id": task.id, "description": task.description, "completed_at": status.completed_at}
        for task, status in (
            db.query(Task, UserTaskStatus)
            .join(UserTaskStatus, UserTaskStatus.id_task == Task.id)
            .filter(UserTaskStatus.id_user == user_id, UserTaskStatus.done == True)
            .all()
        )
    ]

# Mostra as tarefas diárias (de hoje) atribuídas a um utilizador
@router.get("/{user_id}/dailystatus")
def list_today_tasks_with_status(user_id: int, db: Session = Depends(get_db)):
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
def list_not_completed_tasks(user_id: int, db: Session = Depends(get_db)):
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
