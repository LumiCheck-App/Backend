from fastapi import FastAPI
from routes.userRoutes import router as user_router
from routes.tarefasRoutes import router as tarefas_router
from app.routes.digitalHabitRoutes import router as dependencias_router
from routes.trofeusRoutes import router as trofeus_router
from app.routes.questionRoutes import router as perguntas_router
from config import engine
from models.userModel import Base


app = FastAPI()
app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(tarefas_router, prefix="/tarefas", tags=["Tarefas"])
app.include_router(dependencias_router,prefix="/dependencias", tags=["Dependências"])
app.include_router(trofeus_router, prefix="/trofeus", tags=["Troféus"])
app.include_router(perguntas_router, prefix="/perguntas", tags=["Perguntas"])
Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)