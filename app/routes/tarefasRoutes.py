from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models.userModel import User
from models.tarefasModel import Tarefa
from models.status_tarefaModel import UserTarefaStatus
from config import get_db

router = APIRouter()

@router.post("/criar")
def criar_tarefa(descricao: str, db: Session = Depends(get_db)):
    nova_tarefa = Tarefa(descricao=descricao)
    db.add(nova_tarefa)
    db.commit()
    db.refresh(nova_tarefa)
    return {"message": "Tarefa criada com sucesso", "tarefa": nova_tarefa}

@router.delete("/{tarefa_id}")
def eliminar_tarefa(tarefa_id: int, db: Session = Depends(get_db)):
    tarefa = db.query(Tarefa).filter_by(id=tarefa_id).first()
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    db.delete(tarefa)
    db.commit()
    return {"message": f"Tarefa com ID {tarefa_id} foi eliminada com sucesso"}

@router.get("/")
def listar_tarefas(db: Session = Depends(get_db)):
    return db.query(Tarefa).all()

@router.post("/{tarefa_id}/concluir")
def concluir_tarefa(tarefa_id: int, user_id: int, db: Session = Depends(get_db)):
    # Verifica se a tarefa existe
    tarefa = db.query(Tarefa).filter_by(id=tarefa_id).first()
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    # Verifica se o progresso do utilizador já está registrado
    status = db.query(UserTarefaStatus).filter_by(id_user=user_id, id_tarefa=tarefa_id).first()
    if not status:
        # Cria o registro se não existir
        status = UserTarefaStatus(id_user=user_id, id_tarefa=tarefa_id, done=True)
        db.add(status)
    else:
        # Atualiza o estado para concluído
        status.done = True

    db.commit()
    return {"message": "Tarefa marcada como concluída"}

@router.get("/{user_id}/tarefas/concluidas")
def listar_tarefas_concluidas(user_id: int, db: Session = Depends(get_db)):
    tarefas_concluidas = (
        db.query(Tarefa)
        .join(UserTarefaStatus, UserTarefaStatus.id_tarefa == Tarefa.id)
        .filter(UserTarefaStatus.id_user == user_id, UserTarefaStatus.done == True)
        .all()
    )
    return [{"id": tarefa.id, "descricao": tarefa.descricao} for tarefa in tarefas_concluidas]

@router.get("/{user_id}/tarefas/status")
def listar_tarefas_com_status(user_id: int, db: Session = Depends(get_db)):
    tarefas = (
        db.query(
            Tarefa.id,
            Tarefa.descricao,
            UserTarefaStatus.done
        )
        .outerjoin(UserTarefaStatus, (UserTarefaStatus.id_tarefa == Tarefa.id) & (UserTarefaStatus.id_user == user_id))
        .all()
    )
    return [
        {"id": tarefa.id, "descricao": tarefa.descricao, "done": tarefa.done if tarefa.done is not None else False}
        for tarefa in tarefas
    ]

@router.get("/{user_id}/tarefas/nao_concluidas")
def listar_tarefas_nao_concluidas(user_id: int, db: Session = Depends(get_db)):
    tarefas = (
        db.query(
            Tarefa.id,
            Tarefa.descricao
        )
        .outerjoin(UserTarefaStatus, (UserTarefaStatus.id_tarefa == Tarefa.id) & (UserTarefaStatus.id_user == user_id))
        .filter((UserTarefaStatus.done == False) | (UserTarefaStatus.done == None))
        .all()
    )
    return [
        {"id": tarefa.id, "descricao": tarefa.descricao}
        for tarefa in tarefas
    ]