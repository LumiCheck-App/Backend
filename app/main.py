from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import engine
from models.userModel import Base
from routes.userRoutes import router as user_router
from routes.taskRoutes import router as task_router
from routes.digitalHabitRoutes import router as digital_habit_router
from routes.achievementRoutes import router as achievement_router
from routes.questionRoutes import router as question_router
from routes.screentimeRoutes import router as screen_time_router
from sqlalchemy.orm import Session

from sockets_events import sio
import socketio
from sockets_events import register_socket_events 


from cronjob import start_scheduler, assign_daily_tasks, should_assign_tasks_today
scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        if should_assign_tasks_today(session):
            print("⏳ Atribuindo tarefas imediatamente ao iniciar...")
            assign_daily_tasks()

    scheduler = start_scheduler()
    print("✅ Scheduler started.")
    yield
    scheduler.shutdown()
    print("🛑 Scheduler stopped.")

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_socket_events(sio) 
sio_app = socketio.ASGIApp(sio, other_asgi_app=app)

# Include routers
app.include_router(user_router, prefix="/user", tags=["User"])
app.include_router(task_router, prefix="/task", tags=["Task"])
app.include_router(digital_habit_router, prefix="/digital-habits", tags=["Digital Habit"])
app.include_router(achievement_router, prefix="/achievement", tags=["Achievement"])
app.include_router(question_router, prefix="/question", tags=["Question"])
app.include_router(screen_time_router, prefix="/screentime", tags=["Screen Time"])

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(sio_app, host="0.0.0.0", port=port)

