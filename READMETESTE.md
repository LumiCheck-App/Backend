# **Backend do Projeto com FastAPI, PostgreSQL e Alembic**

Este é o backend do projeto desenvolvido em **FastAPI** com **PostgreSQL**, **Alembic** e **TimeScaleDB** para gestão de dados. Este guia descreve como configurar o ambiente, executar o projeto e começar a desenvolver.

---

## **Pré-requisitos**
Certifica-te de que tens os seguintes itens instalados no sistema:
- **Python 3.8+**
- **PostgreSQL**
- **TimeScaleDB**
- **Git**

---

## **Como Configurar o Projeto**

### **1. Clonar o Repositório**
Primeiro, faz clone do repositório para a máquina local:

---

### **2. Criar um Ambiente Virtual**
Cria e ativa um ambiente virtual para gerir as dependências:
```bash
python3 -m venv venv
source venv/bin/activate
```

---

### **3. Criar a Base de Dados**
Executa:
```bash
sudo -u postgres psql
```
Depois cria a base de dados e ativa as extensões:
```sql
CREATE DATABASE lumicheck;
\c lumicheck
CREATE EXTENSION IF NOT EXISTS timescaledb;
\q
```

> **Nota:** Já não precisas criar o `USER`, pois o Alembic cria as tabelas automaticamente.

---

### **4. Instalar as Dependências**
Com o ambiente virtual ativado, instala as dependências do projeto:
```bash
pip install -r requirements.txt
```

Se adicionares novos pacotes, exporta-os para o `requirements.txt`:
```bash
pip freeze > requirements.txt
```

---

## **Configurar as Migrações com Alembic**
Agora, deves configurar o Alembic para gerir as migrações da base de dados.

### **5. Inicializar o Alembic**
```bash
alembic init alembic
```

Isso cria uma pasta `alembic/` no teu projeto.

### **6. Configurar o Alembic**
- **Abre o ficheiro** `alembic.ini`
- **Altera a linha** da conexão com o banco de dados:
```ini
sqlalchemy.url = postgresql://admin:1234@localhost/lumicheck
```
- **No ficheiro `alembic/env.py`**, encontra esta linha:
```python
target_metadata = None
```
- **E substitui por:**
```python
from app.config import Base
target_metadata = Base.metadata
```

---

### **7. Criar a Primeira Migração**
```bash
alembic revision --autogenerate -m "Initial migration"
```

### **8. Aplicar as Migrações**
```bash
alembic upgrade head
```
> **Agora, a base de dados estará configurada e pronta!** 🚀

---

## **Como Executar o Projeto**

### **1. Ativar o Ambiente Virtual**
Certifica-te de que o ambiente virtual está ativo:
```bash
source venv/bin/activate
```

### **2. Executar o Servidor**
Para iniciar o servidor, execute:
```bash
python3 app/main.py
```
O servidor estará disponível em http://127.0.0.1:8000.

---

## **Documentação da API**
- Documentação interativa Swagger UI: http://127.0.0.1:8000/docs
- Alternativa Redoc: http://127.0.0.1:8000/redoc

---

## **Estrutura do Projeto**
```bash
 backend/
├── app/
│   ├── __init__.py      
│   ├── models/          
│   ├── routes/         
│   ├── config.py        
│   ├── main.py          
├── alembic/              # Diretório das migrações
├── .env                 
├── requirements.txt     
├── venv/                
```

---

## **Scripts Úteis**
### **Criar uma Nova Migração**
Sempre que fizeres alterações nos modelos, executa:
```bash
alembic revision --autogenerate -m "Descrição da alteração"
```

### **Aplicar Migrações**
```bash
alembic upgrade head
```

### **Reverter para um Estado Anterior**
```bash
alembic downgrade -1
```

