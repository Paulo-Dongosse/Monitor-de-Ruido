from fastapi.testclient import TestClient
from backend import main

client = TestClient(main.app)

def test_criar_leitura_sem_token():
    payload = {"device_id": "teste", "timestamp": "2025-11-01T00:00:00Z", "nivel_db": 70.5}
    resposta = client.post("/api/leituras", json=payload)
    assert resposta.status_code == 401
