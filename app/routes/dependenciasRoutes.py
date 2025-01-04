from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.userModel import User
from app.models.tarefasModel import Tarefa
from app.models.dependenciaModel import Dependencia
from app.models.status_tarefaModel import UserTarefaStatus
from app.models.user_dependenciasModel import UserDependenciaStatus
from app.config import get_db

router = APIRouter()

@router.post("/criar")
def criar_dependencia(nome: str, db: Session = Depends(get_db)):
    nova_dependencia = Dependencia(nome=nome)
    db.add(nova_dependencia)
    db.commit()
    db.refresh(nova_dependencia)
    return {"message": "Dependência criada com sucesso", "dependencia": nova_dependencia}

@router.get("/")
def listar_dependencias(db: Session = Depends(get_db)):
    return db.query(Dependencia).all()

@router.post("/{user_id}/dependencias/{dependencia_id}")
def associar_dependencia(user_id: int, dependencia_id: int, db: Session = Depends(get_db)):
    # Verifica se a dependência existe
    dependencia = db.query(Dependencia).filter_by(id=dependencia_id).first()
    if not dependencia:
        raise HTTPException(status_code=404, detail="Dependência não encontrada")

    # Verifica se já está associado
    status = db.query(UserDependenciaStatus).filter_by(id_user=user_id, id_dependencia=dependencia_id).first()
    if not status:
        status = UserDependenciaStatus(id_user=user_id, id_dependencia=dependencia_id)
        db.add(status)
        db.commit()
        return {"message": "Dependência associada ao utilizador com sucesso"}

    return {"message": "Dependência já associada ao utilizador"}

@router.delete("/{user_id}/dependencias/{dependencia_id}")
def remover_dependencia(user_id: int, dependencia_id: int, db: Session = Depends(get_db)):
    # Verifica se estão associados
    status = db.query(UserDependenciaStatus).filter_by(id_user=user_id, id_dependencia=dependencia_id).first()
    if not status:
        raise HTTPException(status_code=404, detail="Associação não encontrada")

    db.delete(status)
    db.commit()
    return {"message": "Dependência removida do utilizador com sucesso"}

@router.get("/{user_id}/dependencias")
def listar_dependencias_associadas(user_id: int, db: Session = Depends(get_db)):
    dependencias = (
        db.query(Dependencia)
        .join(UserDependenciaStatus, UserDependenciaStatus.id_dependencia == Dependencia.id)
        .filter(UserDependenciaStatus.id_user == user_id)
        .all()
    )
    return [{"id": dependencia.id, "nome": dependencia.nome} for dependencia in dependencias]

