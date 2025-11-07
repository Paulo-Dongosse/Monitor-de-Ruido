# ===============================
# 🐍 Dockerfile do Backend (API)
# ===============================

# Imagem base do Python
FROM python:3.11

# Diretório de trabalho dentro do container
WORKDIR /app

# Copiar apenas os arquivos necessários
COPY ../requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copiar o conteúdo do backend para dentro do container
COPY . /app

# Expor a porta da API (FastAPI)
EXPOSE 8000

# Comando padrão ao iniciar o container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
