#!/usr/bin/env bash
set -e

echo "=== Setup: Monitor de Ruído ==="
ROOT_DIR="$(pwd)"
PYTHON=python3

# 1) Criar virtualenv
echo "🔧 Criando virtualenv..."
if [ ! -d ".venv" ]; then
  $PYTHON -m venv .venv
fi
# ativa venv (POSIX)
source .venv/bin/activate

# 2) Atualizar pip e instalar dependências necessárias
echo "📦 Instalando dependências Python..."
pip install --upgrade pip
pip install fastapi uvicorn pydantic passlib[bcrypt] pyjwt streamlit requests pandas matplotlib sounddevice numpy pytest fpdf

# 3) Garantir estruturas de pastas
echo "📁 Criando diretórios (se não existirem)..."
mkdir -p backend
mkdir -p dashboard
mkdir -p sensor
mkdir -p backend/tests
mkdir -p reports

# 4) Criar banco e tabelas (usando Python para ser independente do sqlite3 CLI)
DB_PATH="$ROOT_DIR/backend/leituras.db"
echo "🗄️  Criando banco SQLite em: $DB_PATH (se não existir)..."

python - <<PY
import sqlite3, os
db = os.path.join(os.getcwd(), 'backend', 'leituras.db')
conn = sqlite3.connect(db)
c = conn.cursor()
# tabela de leituras
c.execute('''
CREATE TABLE IF NOT EXISTS leituras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT,
    timestamp TEXT,
    nivel_db REAL
)
''')
# tabela de usuários (username + senha hash)
c.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    senha TEXT
)
''')
conn.commit()
conn.close()
print("✅ Banco e tabelas criados/confirmados.")
PY

# 5) Criar usuário admin de desenvolvimento (senha admin123) caso não exista
echo "👤 Criando usuário admin (usuário: admin, senha: admin123) se não existir..."
python - <<PY
import sqlite3, os
from passlib.context import CryptContext
db = os.path.join(os.getcwd(), 'backend', 'leituras.db')
ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
conn = sqlite3.connect(db)
c = conn.cursor()
hash_senha = ctx.hash("admin123")
try:
    c.execute("INSERT INTO usuarios (username, senha) VALUES (?, ?)", ("admin", hash_senha))
    conn.commit()
    print("✅ Usuário admin criado (admin / admin123).")
except sqlite3.IntegrityError:
    print("⚠️ Usuário admin já existe. Pulando criação.")
conn.close()
PY

# 6) Gerar token JWT para o admin e salvar em arquivo
echo "🔑 Gerando token JWT para 'admin' (expira em 30 dias)..."
TOKEN=$(python - <<PY
import jwt, os
from datetime import datetime, timedelta
SECRET_KEY = os.getenv("SECRET_KEY", "segredo_super_secreto")
ALGORITHM = "HS256"
exp = datetime.utcnow() + timedelta(days=30)
token = jwt.encode({"sub":"admin", "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)
# pyjwt retorna bytes em algumas versões; garantir string
if isinstance(token, bytes):
    token = token.decode()
print(token)
PY
)

echo "✅ Token gerado e armazenado em arquivo: backend/admin_token.txt"
echo "$TOKEN" > backend/admin_token.txt

# 7) Injetar token no sensor e dashboard (substitui placeholder SEU_TOKEN_JWT_AQUI)
SENSOR_FILE="$ROOT_DIR/sensor/sensor_noise.py"
DASH_FILE="$ROOT_DIR/dashboard/streamlit_app.py"

if [ -f "$SENSOR_FILE" ]; then
  echo "✏️ Atualizando token no sensor: $SENSOR_FILE"
  # faz backup antes
  cp "$SENSOR_FILE" "$SENSOR_FILE.bak"
  # substitui placeholder pela string token entre aspas
  sed -i "s/SEU_TOKEN_JWT_AQUI/$TOKEN/g" "$SENSOR_FILE" || true
else
  echo "⚠️ Arquivo sensor/sensor_noise.py não encontrado — verifique manualmente."
fi

if [ -f "$DASH_FILE" ]; then
  echo "✏️ Atualizando token no dashboard (se aplicável): $DASH_FILE"
  cp "$DASH_FILE" "$DASH_FILE.bak"
  sed -i "s/SEU_TOKEN_JWT_AQUI/$TOKEN/g" "$DASH_FILE" || true
fi

# 8) Iniciar serviços em background (uvicorn, streamlit e sensor)
echo "▶️ Iniciando backend (uvicorn) em background..."
# logs
mkdir -p logs
nohup .venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 > logs/uvicorn.log 2>&1 &

echo "▶️ Iniciando dashboard (streamlit) em background..."
nohup .venv/bin/streamlit run dashboard/streamlit_app.py --server.port 8501 --server.address 0.0.0.0 > logs/streamlit.log 2>&1 &

# pequeno delay para garantir que backend levantou antes do sensor tentar enviar
sleep 2

echo "▶️ Iniciando sensor em background..."
if [ -f "$SENSOR_FILE" ]; then
  nohup .venv/bin/python "$SENSOR_FILE" > logs/sensor.log 2>&1 &
else
  echo "⚠️ sensor/sensor_noise.py não encontrado — pulei iniciar o sensor."
fi

# 9) Mostrar instruções finais
echo ""
echo "✅ Setup concluído!"
echo "Acesse:"
echo "  • API (Swagger): http://localhost:8000/docs"
echo "  • Dashboard:     http://localhost:8501"
echo ""
echo "Token JWT do admin salvo em: backend/admin_token.txt"
echo ""
echo "Logs:"
echo "  • logs/uvicorn.log"
echo "  • logs/streamlit.log"
echo "  • logs/sensor.log"
echo ""
echo "Se precisar parar os serviços iniciados por este script, execute:"
echo "  pkill -f uvicorn || true"
echo "  pkill -f streamlit || true"
echo "  pkill -f sensor_noise.py || true"
echo ""
echo "Observações:"
echo " - Se estiver no Windows, me avise que eu gero versão 'setup.bat'."
echo " - Se preferir rodar via Docker, recomendo usar docker-compose (eu posso gerar uma versão que inclua o sensor em container)."
