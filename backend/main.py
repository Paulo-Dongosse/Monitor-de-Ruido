import os
import sqlite3
from typing import List
from fastapi import FastAPI, Depends, Request
from pydantic import BaseModel
from datetime import datetime

import auth
from auth_routes import router as auth_router

app = FastAPI(title="Monitor de Ruído", version="1.1")

# Inclui rotas de autenticação
app.include_router(auth_router)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.getenv("DB_FILE", os.path.join("/app/data", "leituras.db"))


# -------------------------------
# Modelos
# -------------------------------
class Leitura(BaseModel):
    device_id: str
    timestamp: str
    nivel_db: float


# -------------------------------
# Banco de Dados
# -------------------------------
def conectar():
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    return sqlite3.connect(DB_FILE)


@app.on_event("startup")
def inicializar_banco():
    print("🔧 Inicializando banco de dados...")

    conn = conectar()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS leituras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            timestamp TEXT,
            nivel_db REAL
        )
    """)
    conn.commit()
    conn.close()

    # Cria usuário admin (se não existir)
    auth.criar_tabelas()
    auth.criar_usuario_desenvolvimento()

    print("✅ Banco de dados e usuário admin prontos!")


# -------------------------------
# Rotas Protegidas (JWT)
# -------------------------------
@app.post("/api/leituras", status_code=201)
def criar_leitura(leitura: Leitura, usuario: str = Depends(auth.verificar_token)):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO leituras (device_id, timestamp, nivel_db) VALUES (?, ?, ?)",
        (leitura.device_id, leitura.timestamp, leitura.nivel_db),
    )
    conn.commit()
    conn.close()
    return {"mensagem": "Leitura registrada com sucesso!"}


@app.get("/api/leituras", response_model=List[Leitura])
def listar_leituras(usuario: str = Depends(auth.verificar_token)):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT device_id, timestamp, nivel_db FROM leituras ORDER BY id DESC LIMIT 50")
    rows = cursor.fetchall()
    conn.close()
    return [Leitura(device_id=row[0], timestamp=row[1], nivel_db=row[2]) for row in rows]


# -------------------------------
# 🔊 Nova Rota — Recebe dados do sensor local
# -------------------------------
@app.post("/api/sensor", status_code=201)
async def receber_sensor(request: Request):
    """Recebe ruído captado pelo microfone local e grava no banco"""
    dados = await request.json()
    device_id = dados.get("device_id", "mic_local")
    nivel_db = dados.get("nivel_db")

    if nivel_db is None:
        return {"erro": "Campo 'nivel_db' é obrigatório."}

    timestamp = datetime.now().isoformat()

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO leituras (device_id, timestamp, nivel_db) VALUES (?, ?, ?)",
        (device_id, timestamp, nivel_db),
    )
    conn.commit()
    conn.close()

    print(f"🎙️ Leitura recebida do sensor: {nivel_db:.2f} dB")
    return {"mensagem": "Leitura do sensor registrada com sucesso!"}
