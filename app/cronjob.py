from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from datetime import datetime
from config import engine
from models import userModel, taskModel, taskStatusModel
import random
from sqlalchemy import func

def assign_missing_tasks():
    print(f"🕒 Verificar tarefas: {datetime.now()}")

    with Session(engine) as session:
        today = datetime.now().date()
        all_tasks = session.query(taskModel.Task).all()

        if len(all_tasks) < 2:
            print("Não há tarefas suficientes para atribuir.")
            return

        users = session.query(userModel.User).all()

        for user in users:
            existing_task_ids = set(
                task_id for (task_id,) in session.query(taskStatusModel.UserTaskStatus.id_task).filter(
                    taskStatusModel.UserTaskStatus.id_user == user.id,
                    taskStatusModel.UserTaskStatus.completed_at == today
                ).all()
            )

            missing_count = 2 - len(existing_task_ids)
            if missing_count <= 0:
                continue 

            available_tasks = [t for t in all_tasks if t.id not in existing_task_ids]
            if len(available_tasks) < missing_count:
                print(f"User {user.id} não tem tarefas disponiveis para atribuir.")
                continue

            new_tasks = random.sample(available_tasks, missing_count)
            for task in new_tasks:
                session.add(taskStatusModel.UserTaskStatus(
                    id_user=user.id,
                    id_task=task.id,
                    done=False,
                    completed_at=today
                ))

        session.commit()
        print("✅ Atribuições completas.")

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(assign_missing_tasks, 'cron', hour=0, minute=0)
    scheduler.start()
    return scheduler
