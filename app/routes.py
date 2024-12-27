from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def home():
    return {"message": "Backend iniciado com FastAPI e PostgreSQL"}