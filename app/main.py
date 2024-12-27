from fastapi import FastAPI
from routes.userRoutes import router
from config import engine
from models.userModel import Base

app = FastAPI()
app.include_router(router)
Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)