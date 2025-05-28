from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from datetime import datetime
from config import engine
from models import userModel, taskModel, taskStatusModel
import random
from sqlalchemy import func

def should_assign_tasks_today(session: Session) -> bool:
    today = datetime.now().date()

    users = session.query(userModel.User).all()
    for user in users:
        existing = session.query(taskStatusModel.UserTaskStatus).filter(
            taskStatusModel.UserTaskStatus.id_user == user.id,
            taskStatusModel.UserTaskStatus.completed_at == today
        ).count()

        if existing < 2:
            return True  # Pelo menos um utilizador ainda não tem 2 tarefas

    return False  # Todos os utilizadores têm 2 ou mais tarefas para hoje


def assign_daily_tasks():
    print(f"Running task assignment: {datetime.now()}")

    with Session(engine) as session:
        users = session.query(userModel.User).all()
        all_tasks = session.query(taskModel.Task).all()

        if len(all_tasks) < 2:
            print("Not enough tasks available.")
            return

        for user in users:
            # Evita duplicar tarefas no mesmo dia
            today = datetime.now().date()
            existing = session.query(taskStatusModel.UserTaskStatus).filter(
                taskStatusModel.UserTaskStatus.id_user == user.id,
                taskStatusModel.UserTaskStatus.completed_at == today
            ).all()
            if len(existing) >= 2:
                continue

            user_tasks = random.sample(all_tasks, 2)
            for task in user_tasks:
                task_status = taskStatusModel.UserTaskStatus(
                    id_user=user.id,
                    id_task=task.id,
                    done=False,
                    completed_at=today
                )
                session.add(task_status)
        session.commit()
        print("Tasks assigned.")

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(assign_daily_tasks, 'cron', hour=0, minute=0)
    # scheduler.add_job(assign_daily_tasks, 'interval', minutes=1)  # For testing
    scheduler.start()
    return scheduler
