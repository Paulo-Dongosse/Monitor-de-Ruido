import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from datetime import datetime
import time
from zoneinfo import ZoneInfo

# -----------------------------
# CONFIGURAÇÕES GERAIS
# -----------------------------
API_BASE = "http://backend:8000"
LOGIN_URL = f"{API_BASE}/auth/login"
DATA_URL = f"{API_BASE}/api/leituras"

LIMITE_DB = 80          # limite de alerta de ruído
MAX_REGISTROS = 500     # máximo de registros para exibição
COR_PRINCIPAL = "#0066cc"
TZ_LOCAL = ZoneInfo("America/Sao_Paulo")

plt.style.use("seaborn-v0_8-whitegrid")

st.set_page_config(
    page_title="Monitor de Ruído",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Monitor de Ruído - Dashboard")
st.markdown("Visualize em tempo real os níveis de ruído captados pelos sensores.")

# -----------------------------
# FUNÇÕES AUXILIARES
# -----------------------------
@st.cache_data(ttl=3600)
def autenticar():
    dados = {"username": "admin", "password": "admin123"}
    try:
        resposta = requests.post(LOGIN_URL, json=dados, timeout=10)
        resposta.raise_for_status()
        return resposta.json()["access_token"]
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erro ao autenticar: {e}")
        return None


@st.cache_data(ttl=60)
def carregar_dados(token: str):
    """
    Busca leituras da API e converte timestamps para America/Sao_Paulo.
    Se timestamp for naive (sem timezone) assume que veio em UTC e converte.
    """
    if not token:
        return pd.DataFrame()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resposta = requests.get(DATA_URL, headers=headers, timeout=10)
        resposta.raise_for_status()
        dados = resposta.json()
        df = pd.DataFrame(dados)
        if df.empty:
            return df

        # Converte para datetime (pandas detecta timezone se houver)
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

        # Função que garante timezone-aware em TZ_LOCAL
        def _to_local(ts):
            if pd.isna(ts):
                return pd.NaT
            # se não for Timestamp (por segurança), converte
            if not isinstance(ts, pd.Timestamp):
                try:
                    ts = pd.Timestamp(ts)
                except Exception:
                    return pd.NaT
            # se naive -> assume UTC e localiza
            if ts.tzinfo is None:
                try:
                    ts = ts.tz_localize("UTC")
                except Exception:
                    # fallback: return NaT se não conseguir localizar
                    return pd.NaT
            # converte para o fuso local
            try:
                return ts.tz_convert(TZ_LOCAL)
            except Exception:
                return pd.NaT

        df["timestamp"] = df["timestamp"].apply(_to_local)

        # remove inválidos e ordena
        df = df.dropna(subset=["timestamp"]).sort_values("timestamp")
        return df
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erro ao buscar dados: {e}")
        return pd.DataFrame()


def exibir_metricas(df):
    col1, col2, col3 = st.columns(3)
    col1.metric("🔈 Nível Médio", f"{df['nivel_db'].mean():.1f} dB")
    col2.metric("📉 Mínimo", f"{df['nivel_db'].min():.1f} dB")
    col3.metric("📈 Máximo", f"{df['nivel_db'].max():.1f} dB")


def exibir_alerta(df):
    if df["nivel_db"].max() > LIMITE_DB:
        st.warning(f"🚨 Alerta! Nível de ruído acima de {LIMITE_DB} dB detectado.")


def formatar_tabela(df):
    # garante que timestamp esteja em TZ_LOCAL e formatado corretamente
    def _fmt_ts(t):
        if pd.isna(t):
            return ""
        try:
            if isinstance(t, pd.Timestamp) and t.tzinfo is not None:
                t_local = t.astimezone(TZ_LOCAL)
                return t_local.strftime("%d/%m/%Y %H:%M:%S")
            else:
                # tentativa segura
                return pd.Timestamp(t).strftime("%d/%m/%Y %H:%M:%S")
        except Exception:
            return str(t)

    return df.style.format({
        "nivel_db": "{:.2f}",
        "timestamp": _fmt_ts
    })


# -----------------------------
# AUTENTICAÇÃO
# -----------------------------
token = autenticar()
if not token:
    st.stop()

# -----------------------------
# CONTROLES LATERAIS
# -----------------------------
st.sidebar.header("⚙️ Configurações")
atualizar = st.sidebar.checkbox("🔄 Atualizar automaticamente", value=True)
intervalo = st.sidebar.slider("⏱️ Intervalo (segundos)", 1, 60, 5)

# -----------------------------
# CARREGAR DADOS
# -----------------------------
df = carregar_dados(token)

if df.empty:
    st.warning("Nenhuma leitura registrada até o momento.")
    st.stop()

# -----------------------------
# FILTRO DE DATAS
# -----------------------------
col1, col2 = st.columns(2)
with col1:
    inicio = st.date_input("Início", value=df["timestamp"].min().date(), key="inicio_filtro")
with col2:
    fim = st.date_input("Fim", value=df["timestamp"].max().date(), key="fim_filtro")

df_filtrado = df[
    (df["timestamp"].dt.date >= inicio) &
    (df["timestamp"].dt.date <= fim)
]

if len(df_filtrado) > MAX_REGISTROS:
    df_filtrado = df_filtrado.tail(MAX_REGISTROS)

# -----------------------------
# CABEÇALHO DE MÉTRICAS
# -----------------------------
st.markdown("### 📊 Estatísticas Gerais")
exibir_metricas(df_filtrado)
exibir_alerta(df_filtrado)

# -----------------------------
# TABELA DE DADOS
# -----------------------------
st.markdown("### 📋 Leituras Registradas")
st.dataframe(formatar_tabela(df_filtrado), use_container_width=True, height=300)

# -----------------------------
# ABAS DE GRÁFICOS
# -----------------------------
st.markdown("### 📈 Visualizações dos Níveis de Ruído")
aba_linha, aba_barras, aba_dispersao = st.tabs(["📈 Linha", "📊 Barras", "🔹 Dispersão"])

# 📈 Linha
with aba_linha:
    fig, ax = plt.subplots(figsize=(14, 4))
    ax.plot(df_filtrado["timestamp"], df_filtrado["nivel_db"], color=COR_PRINCIPAL, marker="o", linewidth=1)
    ax.set_xlabel("Horário")
    ax.set_ylabel("Nível (dB)")
    ax.set_title("Histórico de Ruído em Tempo Real")
    plt.xticks(rotation=30)
    if len(df_filtrado) > 30:
        ax.set_xlim(df_filtrado["timestamp"].iloc[-30], df_filtrado["timestamp"].iloc[-1])
    st.pyplot(fig, use_container_width=True)

# 📊 Barras
with aba_barras:
    cmap = LinearSegmentedColormap.from_list("azul_gradiente", ["#cce0ff", COR_PRINCIPAL])
    min_val, max_val = df_filtrado["nivel_db"].min(), df_filtrado["nivel_db"].max()
    cores = [cmap((v - min_val) / (max_val - min_val + 1e-6)) for v in df_filtrado["nivel_db"]]

    fig_bar, ax_bar = plt.subplots(figsize=(14, 4))
    ax_bar.bar(
        df_filtrado["timestamp"].dt.strftime("%H:%M:%S"),
        df_filtrado["nivel_db"],
        color=cores,
        width=0.7
    )
    ax_bar.set_xlabel("Horário")
    ax_bar.set_ylabel("Nível (dB)")
    ax_bar.set_title("Leituras de Ruído — Intensidade em Tons de Azul")
    plt.xticks(rotation=45)
    st.pyplot(fig_bar, use_container_width=True)

# 🔹 Dispersão
with aba_dispersao:
    fig_scatter, ax_scatter = plt.subplots(figsize=(14, 4))
    scatter = ax_scatter.scatter(
        df_filtrado["timestamp"],
        df_filtrado["nivel_db"],
        c=df_filtrado["nivel_db"],
        cmap="coolwarm",
        alpha=0.8,
        edgecolors="k"
    )
    ax_scatter.set_xlabel("Horário")
    ax_scatter.set_ylabel("Nível (dB)")
    ax_scatter.set_title("Dispersão dos Níveis de Ruído ao Longo do Tempo")
    plt.xticks(rotation=30)
    plt.colorbar(scatter, ax=ax_scatter, label="Intensidade (dB)")
    st.pyplot(fig_scatter, use_container_width=True)

# -----------------------------
# RODAPÉ
# -----------------------------
ultimo = df_filtrado["timestamp"].max()
if pd.notna(ultimo):
    # garante exibição em fuso local
    try:
        ultimo_local = ultimo.astimezone(TZ_LOCAL) if ultimo.tzinfo is not None else pd.Timestamp(ultimo).tz_localize("UTC").tz_convert(TZ_LOCAL)
        st.caption(f"📅 Última atualização: {ultimo_local.strftime('%d/%m/%Y %H:%M:%S')}")
    except Exception:
        st.caption(f"📅 Última atualização: {str(ultimo)}")

# -----------------------------
# ATUALIZAÇÃO AUTOMÁTICA
# -----------------------------
if atualizar:
    time.sleep(intervalo)
    st.experimental_rerun()
