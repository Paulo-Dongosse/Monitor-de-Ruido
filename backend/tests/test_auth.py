from fastapi.testclient import TestClient
from backend import main

client = TestClient(main.app)

def test_listar_leituras_sem_token():
    resposta = client.get("/api/leituras")
    assert resposta.status_code == 401
