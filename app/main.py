from fastapi import FastAPI
from app.routes.userRoutes import router as user_router
from app.routes.tarefasRoutes import router as tarefas_router
from app.routes.dependenciasRoutes import router as dependencias_router
from app.routes.trofeusRoutes import router as trofeus_router
from app.routes.perguntasRoutes import router as perguntas_router
from app.config import engine
from app.models.userModel import Base
from app import main
import uvicorn
import os


app = FastAPI()
app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(tarefas_router, prefix="/tarefas", tags=["Tarefas"])
app.include_router(dependencias_router,prefix="/dependencias", tags=["Dependências"])
app.include_router(trofeus_router, prefix="/trofeus", tags=["Troféus"])
app.include_router(perguntas_router, prefix="/perguntas", tags=["Perguntas"])
Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 1234))  # Porta padrão fornecida pelo Railway
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)