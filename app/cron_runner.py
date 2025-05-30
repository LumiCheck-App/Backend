from cronjob import start_scheduler, assign_daily_tasks, should_assign_tasks_today
from config import engine
from sqlalchemy.orm import Session
from models.userModel import Base

if __name__ == "__main__":
    print("🎯 Starting Cron Job Runner...")
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        if should_assign_tasks_today(session):
            print("⏳ Atribuindo tarefas imediatamente ao iniciar...")
            assign_daily_tasks()

    scheduler = start_scheduler()
    print("✅ Scheduler started and running...")

    # Impede o script de encerrar (mantém o scheduler ativo)
    try:
        import time
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        scheduler.shutdown()
        print("🛑 Scheduler stopped.")
