# ===================================
# 📊 Dockerfile do Dashboard (Streamlit)
# ===================================

FROM python:3.11

WORKDIR /app

# Copiar e instalar dependências
COPY ../requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copiar o código do dashboard
COPY . /app

# Expor a porta do Streamlit
EXPOSE 8501

# Comando para rodar o Streamlit
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
