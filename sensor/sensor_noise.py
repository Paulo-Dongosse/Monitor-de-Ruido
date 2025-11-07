import sounddevice as sd
import numpy as np
import requests
import time
from datetime import datetime

# URL do backend rodando (via Docker)
# Se estiver rodando o sensor fora do Docker (na sua máquina):
API_URL = "http://localhost:8000/api/sensor"

# Se o sensor rodar dentro do Docker, use o nome do serviço:
# API_URL = "http://backend:8000/api/sensor"

DEVICE_ID = "mic_local"

def medir_ruido(duracao=1, taxa_amostragem=44100):
    """Captura o som ambiente e retorna o nível em decibéis (dB)."""
    audio = sd.rec(int(duracao * taxa_amostragem), samplerate=taxa_amostragem, channels=1, dtype='float64')
    sd.wait()
    rms = np.sqrt(np.mean(audio**2))
    db = 20 * np.log10(rms + 1e-6)
    return round(db, 2)

def enviar_leitura(valor_db):
    """Envia o valor captado para a API FastAPI."""
    try:
        dados = {
            "device_id": DEVICE_ID,
            "timestamp": datetime.now().isoformat(),
            "nivel_db": valor_db
        }
        response = requests.post(API_URL, json=dados)
        if response.status_code == 201:
            print(f"✅ Enviado {valor_db} dB com sucesso!")
        else:
            print(f"⚠️ Falha ao enviar ({response.status_code}): {response.text}")
    except Exception as e:
        print("❌ Erro ao enviar leitura:", e)

if __name__ == "__main__":
    print("🎤 Iniciando sensor de ruído...")
    while True:
        nivel = medir_ruido()
        print(f"📡 Nível de ruído: {nivel} dB")
        enviar_leitura(nivel)
        time.sleep(5)  # aguarda 5 segundos entre medições
