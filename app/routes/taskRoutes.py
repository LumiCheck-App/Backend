from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models.userModel import User
from models.taskModel import Task
from models.taskStatusModel import UserTaskStatus
from config import get_db

router = APIRouter()

# Cria uma nova tarefa
@router.post("/create")
def create_task(description: str, db: Session = Depends(get_db)):
    new_task = Task(description=description)
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

# Marca uma tarefa como completa
@router.post("/{task_id}/complete")
def complete_task(task_id: int, user_id: int, db: Session = Depends(get_db)):
    # Verifica se a tarefa existe
    task = db.query(Task).filter_by(id=task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Verifica se o progresso do utilizador já está registrado
    status = db.query(UserTaskStatus).filter_by(id_user=user_id, id_task=task_id).first()
    if not status:
        # Cria o registro se não existir
        status = UserTaskStatus(id_user=user_id, id_task=task_id, done=True)
        db.add(status)
    else:
        # Atualiza o estado para concluído
        status.done = True

    db.commit()
    return {"message": "Task marked as completed"}

# Mostra as tarefas concluidas por um utilizador
@router.get("/{user_id}/completed")
def list_completed_tasks(user_id: int, db: Session = Depends(get_db)):
    completed_tasks = (
        db.query(Task)
        .join(UserTaskStatus, UserTaskStatus.id_task == Task.id)
        .filter(UserTaskStatus.id_user == user_id, UserTaskStatus.done == True)
        .all()
    )
    return [{"id": task.id, "description": task.description} for task in completed_tasks]

# Mostra as tarefas de um utilizador (feitas ou não)
@router.get("/{user_id}/status")
def list_tasks_with_status(user_id: int, db: Session = Depends(get_db)):
    tasks = (
        db.query(
            Task.id,
            Task.description,
            UserTaskStatus.done
        )
        .outerjoin(UserTaskStatus, (UserTaskStatus.id_task == Task.id) & (UserTaskStatus.id_user == user_id))
        .all()
    )
    return [
        {"id": task.id, "description": task.description, "done": task.done if task.done is not None else False}
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
