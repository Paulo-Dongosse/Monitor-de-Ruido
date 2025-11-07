import os
import sqlite3
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.hash import bcrypt

# ------------------------------
# Configurações
# ------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "segredo_super_secreto")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
DB_FILE = os.getenv("DB_FILE", "/app/data/database.db")

security = HTTPBearer()


# ------------------------------
# Funções de banco
# ------------------------------
def conectar_banco():
    """Cria conexão com o banco SQLite"""
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    return sqlite3.connect(DB_FILE, check_same_thread=False)


def criar_tabelas():
    """Cria tabela de usuários se não existir"""
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def criar_usuario_desenvolvimento():
    """Cria o usuário admin padrão, se não existir"""
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE username = ?", ("admin",))
    if cursor.fetchone() is None:
        senha_hash = bcrypt.hash("admin123")
        cursor.execute(
            "INSERT INTO usuarios (username, password) VALUES (?, ?)",
            ("admin", senha_hash)
        )
        conn.commit()
        print("✅ Usuário admin criado com sucesso (username: admin / senha: admin123)")
    else:
        print("⚠️ Usuário admin já existe.")
    conn.close()


# ------------------------------
# Funções de autenticação
# ------------------------------
def autenticar_usuario(username: str, senha: str):
    """Verifica usuário e senha e retorna o username autenticado"""
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM usuarios WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if not row or not bcrypt.verify(senha, row[0]):
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos")

    return username


def gerar_token(username: str):
    """Gera um token JWT válido por tempo definido"""
    expira = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expira}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def verificar_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Valida o token JWT enviado no header Authorization"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
