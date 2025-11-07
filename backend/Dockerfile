FROM python:3.11

WORKDIR /app

COPY . /app

# Instalar dependências corrigidas
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    sqlalchemy \
    fastapi-pagination \
    pytest \
    PyJWT \
    passlib[bcrypt] \
    bcrypt==4.0.1

# Criar pasta de dados
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
