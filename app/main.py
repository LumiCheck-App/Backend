from fastapi import FastAPI
from routes.userRoutes import router as user_router
from routes.taskRoutes import router as task_router
from routes.digitalHabitRoutes import router as digital_habit_router
from routes.achievementRoutes import router as achievement_router
from routes.questionRoutes import router as question_router
from routes.screentimeRoutes import router as screen_time_router
from config import engine
from models.userModel import Base


app = FastAPI()
app.include_router(user_router, prefix="/user", tags=["User"])
app.include_router(task_router, prefix="/task", tags=["Task"])
app.include_router(digital_habit_router,prefix="/digital-habits", tags=["Digital Habit"])
app.include_router(achievement_router, prefix="/achievement", tags=["Achievement"])
app.include_router(question_router, prefix="/question", tags=["Question"])
app.include_router(screen_time_router, prefix="/screentime", tags=["Screen Time"])
Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)