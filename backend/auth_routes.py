from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import auth

router = APIRouter(prefix="/auth", tags=["Autenticação"])


class LoginData(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(dados: LoginData):
    try:
        # Verifica se o usuário e senha estão corretos
        usuario = auth.autenticar_usuario(dados.username, dados.password)
        # Gera o token JWT
        token = auth.gerar_token(usuario)
        return {"access_token": token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
