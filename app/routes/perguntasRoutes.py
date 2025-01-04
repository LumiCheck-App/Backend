from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models.perguntaModel import Pergunta
from models.user_perguntas import UserPerguntaStatus
from config import get_db

router = APIRouter()

# Criar uma nova pergunta
@router.post("/criar")
def criar_pergunta(pergunta: str, db: Session = Depends(get_db)):
    nova_pergunta = Pergunta(pergunta=pergunta)
    db.add(nova_pergunta)
    db.commit()
    db.refresh(nova_pergunta)
    return {"message": "Pergunta criada com sucesso", "pergunta": nova_pergunta}

# Listar todas as perguntas
@router.get("/")
def listar_perguntas(db: Session = Depends(get_db)):
    return db.query(Pergunta).all()

# Adicionar status para uma pergunta específica de um usuário
@router.post("/status")
def adicionar_status_pergunta(id_user: int, id_pergunta: int, resposta: int, db: Session = Depends(get_db)):
    if not (0 <= resposta <= 5):
        raise HTTPException(status_code=400, detail="A resposta deve estar entre 0 e 5")
    
    status = UserPerguntaStatus(id_user=id_user, id_pergunta=id_pergunta, resposta=resposta)
    db.add(status)
    db.commit()
    return {"message": "Status da pergunta adicionado com sucesso"}

# Atualizar status de uma pergunta
@router.put("/status")
def atualizar_status_pergunta(id_user: int, id_pergunta: int, resposta: int, db: Session = Depends(get_db)):
    status = db.query(UserPerguntaStatus).filter_by(id_user=id_user, id_pergunta=id_pergunta).first()
    if not status:
        raise HTTPException(status_code=404, detail="Status não encontrado")
    
    if not (0 <= resposta <= 6):
        raise HTTPException(status_code=400, detail="A resposta deve estar entre 0 e 6")
    
    status.resposta = resposta
    db.commit()
    return {"message": "Status da pergunta atualizado com sucesso"}

# Listar todas as respostas de um usuário com as perguntas associadas
@router.get("/{id_user}/perguntas/respostas")
def listar_respostas_user(id_user: int, db: Session = Depends(get_db)):
    respostas = (
        db.query(UserPerguntaStatus, Pergunta)
        .join(Pergunta, UserPerguntaStatus.id_pergunta == Pergunta.id)
        .filter(UserPerguntaStatus.id_user == id_user)
        .all()
    )
    return [
        {"id_pergunta":pergunta.id ,"pergunta": pergunta.pergunta, "resposta": status.resposta}
        for status, pergunta in respostas
    ]


# Apagar uma pergunta
@router.delete("/{id_pergunta}")
def apagar_pergunta(id_pergunta: int, db: Session = Depends(get_db)):
    pergunta = db.query(Pergunta).filter_by(id=id_pergunta).first()
    if not pergunta:
        raise HTTPException(status_code=404, detail="Pergunta não encontrada")
    
    db.delete(pergunta)
    db.commit()
    return {"message": f"Pergunta com ID {id_pergunta} apagada com sucesso"}
