from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models.userModel import User
from app.models.taskModel import Tarefa
from app.models.digitalHabitModel import Dependencia
from app.models.taskStatusModel import UserTarefaStatus
from app.models.userDigitalHabitModel import UserDependenciaStatus
from app.models.achievementModel import Trofeu
from app.models.achievementStatusModel import UserTrofeuStatus
from config import get_db

router = APIRouter()

@router.get("/")
def listar_trofeus(db: Session = Depends(get_db)):
    return db.query(Trofeu).all()


@router.post("/criar")
def criar_trofeu(nome: str, descricao: str, tag: str, imagem: str = None, db: Session = Depends(get_db)):
    novo_trofeu = Trofeu(nome=nome, descricao=descricao, tag=tag, imagem=imagem)
    db.add(novo_trofeu)
    db.commit()
    db.refresh(novo_trofeu)
    return {"message": "Troféu criado com sucesso", "trofeu": novo_trofeu}

@router.put("/{trofeu_id}")
def atualizar_trofeu(trofeu_id: int, nome: str = None, descricao: str = None, tag: str = None, imagem: str = None, db: Session = Depends(get_db)):
    trofeu = db.query(Trofeu).filter_by(id=trofeu_id).first()
    if not trofeu:
        raise HTTPException(status_code=404, detail="Troféu não encontrado")

    if nome:
        trofeu.nome = nome
    if descricao:
        trofeu.descricao = descricao
    if tag:
        trofeu.tag = tag
    if imagem:
        trofeu.imagem = imagem

    db.commit()
    db.refresh(trofeu)
    return {"message": "Troféu atualizado com sucesso", "trofeu": trofeu}

@router.delete("/{trofeu_id}")
def eliminar_trofeu(trofeu_id: int, db: Session = Depends(get_db)):
    trofeu = db.query(Trofeu).filter_by(id=trofeu_id).first()
    if not trofeu:
        raise HTTPException(status_code=404, detail="Troféu não encontrado")

    db.delete(trofeu)
    db.commit()
    return {"message": "Troféu eliminado com sucesso"}



@router.post("/{user_id}/trofeus/{trofeu_id}/conquistar")
def conquistar_trofeu(user_id: int, trofeu_id: int, db: Session = Depends(get_db)):
    # Verifica se o troféu existe
    trofeu = db.query(Trofeu).filter_by(id=trofeu_id).first()
    if not trofeu:
        raise HTTPException(status_code=404, detail="Troféu não encontrado")

    # Verifica se o status já existe
    status = db.query(UserTrofeuStatus).filter_by(id_user=user_id, id_trofeu=trofeu_id).first()
    if not status:
        # Cria o status se não existir
        status = UserTrofeuStatus(id_user=user_id, id_trofeu=trofeu_id, done=True)
        db.add(status)
    else:
        # Atualiza o status para conquistado
        status.done = True

    db.commit()
    return {"message": "Troféu marcado como conquistado"}

@router.get("/{user_id}/trofeus_conquistados")
def listar_trofeus_conquistados(user_id: int, db: Session = Depends(get_db)):
    trofeus = (
        db.query(Trofeu)
        .join(UserTrofeuStatus, UserTrofeuStatus.id_trofeu == Trofeu.id)
        .filter(UserTrofeuStatus.id_user == user_id, UserTrofeuStatus.done == True)
        .all()
    )
    return [{"id": trofeu.id, "nome": trofeu.nome, "descricao": trofeu.descricao} for trofeu in trofeus]

@router.get("/{user_id}/trofeus/status")
def listar_trofeus_com_status(user_id: int, db: Session = Depends(get_db)):
    trofeus = (
        db.query(
            Trofeu.id,
            Trofeu.nome,
            Trofeu.descricao,
            UserTrofeuStatus.done
        )
        .outerjoin(UserTrofeuStatus, (UserTrofeuStatus.id_trofeu == Trofeu.id) & (UserTrofeuStatus.id_user == user_id))
        .all()
    )
    return [
        {"id": trofeu.id, "nome": trofeu.nome, "descricao": trofeu.descricao, "conquistado": True if trofeu.done else False}
        for trofeu in trofeus
    ]

