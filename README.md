# **Backend do Projeto com FastAPI e PostgreSQL**

Este é o backend do projeto desenvolvido em **FastAPI** com **PostgreSQL** para gestão de dados. Este guia descreve como configurar o ambiente, executar o projeto e começar a desenvolver.

---

## **Pré-requisitos**
Certifica-te de que tem os seguintes itens instalados no seu sistema:
- **Python 3.8+**
- **PostgreSQL**
- **Git**

---

## **Como Configurar o Projeto**

### **1. Clone do Repositório**
Primeiro, faz clone do repositório para a máquina local.

### **2. Cria um ambiente Virtual**
Cria e ativa um ambiente virtual para gerir as dependencias
```bash 
python3 -m venv venv
source venv/bin/activate
```

### **3. Instala as dependências**
Com o ambiente virtual ativado, instala as dependências do projeto:
```bash 
pip install -r requirements.txt
```


## Como executar o projeto

### **1. Ativa o ambiente virtual**
Certifica-te de que o ambiente virtual está ativo:
```bash
source venv/bin/activate
```

### **2. Executa o Servidor**
Para iniciar o servidor, execute:
```bash
python3 app/main.py
```
O servidor estará disponível em http://127.0.0.1:8000.


## Documentação da API
- Documentação interativa Swagger UI: http://127.0.0.1:8000/docs
- Alternativa Redoc: http://127.0.0.1:8000/redoc

## Estrutura do projeto
```bash
 backend/
├── app/
│   ├── __init__.py      
│   ├── models/          
│   ├── routes/         
│   ├── config.py        
│   ├── main.py          
├── .env                 
├── requirements.txt     
├── venv/                
```


## Scripts úteis
### Exportar Dependências
Se adicionares novos pacotes, exporta-os para o requirements.txt:
```bash
pip freeze > requirements.txt
```
