import pandas as pd
import streamlit as st

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="Escala de Ministérios", layout="wide")

# CSS: melhor para celular + layout
st.markdown(
    """
    <style>
      @media (max-width: 768px) {
        .block-container { padding-top: 1rem; padding-left: 0.8rem; padding-right: 0.8rem; }
        h1 { font-size: 1.4rem !important; }
        h2, h3 { font-size: 1.1rem !important; }
      }
      .stDataFrame { width: 100%; }
    </style>
    """,
    unsafe_allow_html=True
)

# 🔗 Link CSV publicado
csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTtu-b1fJg3AaYjKpcmYvdB1AaZpWGTRPr76mBxyBczreE69_A_3_NLJ4OPuGMtefWyTzl56G0oklFo/pub?output=csv"

# =============================
# LOAD + TRANSFORM
# =============================
@st.cache_data(ttl=300)
def carregar_dados(url: str) -> pd.DataFrame:
    # header=1 porque seu CSV tem a linha do cabeçalho na segunda linha
    df = pd.read_csv(url, header=1)
    df.columns = df.columns.str.strip()

    # Converter Data
    df["Data"] = pd.to_datetime(df["Data"], dayfirst=True, errors="coerce")

    # Colunas de ministérios = tudo menos "Data"
    ministerios_cols = [c for c in df.columns if c != "Data"]

    # Wide -> Long
    melted = df.melt(
        id_vars=["Data"],
        value_vars=ministerios_cols,
        var_name="Ministerio",
        value_name="Nome",
    )

    # Remover vazios
    melted = melted.dropna(subset=["Nome"])

    # Suportar múltiplos nomes por célula:
    # "João e Maria" ou "João, Maria" (e também ";" como bônus)
    melted["Nome"] = melted["Nome"].astype(str)
    melted["Nome"] = melted["Nome"].str.replace(r"\s+[eE]\s+", ",", regex=True)
    melted["Nome"] = melted["Nome"].str.replace(";", ",", regex=False)

    # Split por vírgula e explode
    melted["Nome"] = melted["Nome"].str.split(",")
    melted = melted.explode("Nome")
    melted["Nome"] = melted["Nome"].str.strip()
    melted = melted[melted["Nome"] != ""]

    # Padroniza nomes (evita JOAO/Joao/joao)
    melted["Nome"] = melted["Nome"].str.title()

    # Ano e mês
    melted["Ano"] = melted["Data"].dt.year
    melted["Mes"] = melted["Data"].dt.month

    return melted

df_melted = carregar_dados(csv_url)

# =============================
# CORES POR MINISTÉRIO (tabela detalhada)
# =============================
MINISTERIO_CORES = {
    "Animação": "#E3F2FD",      # azul claro
    "Condução": "#E8F5E9",      # verde claro
    "Dança": "#FCE4EC",         # rosa claro
    "Pregação": "#FFF3E0",      # laranja claro
    "Comunicação": "#F3E5F5",   # roxo claro
}

def estilo_por_ministerio(row):
    cor = MINISTERIO_CORES.get(row.get("Ministerio", ""), "#FFFFFF")
    return [f"background-color: {cor};"] * len(row)

def criar_styler(df_exibicao: pd.DataFrame):
    styler = (
        df_exibicao.style
        .apply(estilo_por_ministerio, axis=1)
        .set_table_styles([
            {"selector": "th", "props": [("font-weight", "600"), ("text-align", "left")]},
            {"selector": "td", "props": [("padding", "10px 10px"), ("text-align", "left")]},
            {"selector": "table", "props": [("width", "100%")]},
        ])
    )
    # Esconder índice (compatível com versões diferentes)
    try:
        styler = styler.hide(axis="index")
    except Exception:
        styler = styler.hide_index()
    return styler

def safe_dataframe(data, **kwargs):
    """Compatibilidade: hide_index pode não existir em versões antigas."""
    try:
        st.dataframe(data, **kwargs)
    except TypeError:
        kwargs.pop("hide_index", None)
        st.dataframe(data, **kwargs)

# =============================
# RESUMO DE GRUPOS (por Data) COM SERVOS POR MINISTÉRIO
# =============================
def montar_resumo_grupos(df_long: pd.DataFrame) -> pd.DataFrame:
    """
    Retorna um DF com:
      Data_dt (datetime)
      Data (string DD/MM/AAAA)
      Ministérios (lista única)
      Servos (texto com 'Ministério: nomes')
    """
    df_ok = df_long.dropna(subset=["Data"]).copy()
    df_ok["Data_dt"] = df_ok["Data"].dt.normalize()

    rows = []
    for data_dt, g in df_ok.groupby("Data_dt"):
        # ministérios do dia
        ministerios = " | ".join(sorted(set(g["Ministerio"].astype(str))))

        # servos vinculados ao ministério certinho
        linhas = []
        for m, sub in g.groupby("Ministerio"):
            servos = ", ".join(sorted(set(sub["Nome"].astype(str))))
            linhas.append(f"{m}: {servos}")

        servos_map = "\n".join(linhas)

        rows.append({
            "Data_dt": data_dt,
            "Data": pd.to_datetime(data_dt).strftime("%d/%m/%Y"),
            "Ministérios": ministerios,
            "Servos": servos_map
        })

    return pd.DataFrame(rows).sort_values("Data_dt")

def separar_proximos_ultimos(resumo: pd.DataFrame):
    hoje = pd.Timestamp.now().normalize()

    futuros = resumo[resumo["Data_dt"] >= hoje].sort_values("Data_dt")
    passados = resumo[resumo["Data_dt"] < hoje].sort_values("Data_dt")

    proximo = futuros.head(1)
    proximos3 = futuros.head(3)
    ultimos5 = passados.tail(5)

    # Só colunas pedidas
    cols = ["Data", "Ministérios", "Servos"]
    return proximo[cols], proximos3[cols], ultimos5[cols]

# =============================
# UI
# =============================
st.title("📅 Escala de Ministérios")

# Legenda de cores (para o detalhado)
with st.expander("🎨 Legenda de cores por ministério (tabela detalhada)", expanded=False):
    cols = st.columns(3)
    for i, (m, cor) in enumerate(MINISTERIO_CORES.items()):
        with cols[i % 3]:
            st.markdown(
                f"""
                <div style="display:flex;align-items:center;gap:10px;margin:6px 0;">
                  <div style="width:18px;height:18px;border-radius:6px;background:{cor};border:1px solid #ddd;"></div>
                  <div style="font-size:14px;">{m}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

# =============================
# BLOCO INICIAL (como você pediu)
# =============================
resumo = montar_resumo_grupos(df_melted)
proximo_df, proximos3_df, ultimos5_df = separar_proximos_ultimos(resumo)

st.subheader("➡️ Próximo Grupo")
if proximo_df.empty:
    st.info("Não encontrei um próximo grupo (nenhuma data futura a partir de hoje).")
else:
    safe_dataframe(proximo_df, hide_index=True, use_container_width=True)

st.subheader("⏭️ Próximos 3 Grupos")
if proximos3_df.empty:
    st.info("Não encontrei próximos grupos (nenhuma data futura a partir de hoje).")
else:
    safe_dataframe(proximos3_df, hide_index=True, use_container_width=True)

st.subheader("⬅️ Últimos 5 Grupos")
if ultimos5_df.empty:
    st.info("Não encontrei grupos anteriores (nenhuma data antes de hoje).")
else:
    safe_dataframe(ultimos5_df, hide_index=True, use_container_width=True)

st.divider()

# =============================
# FILTROS (mantendo como estava, com "Todos")
# =============================
st.subheader("🔎 Filtros")

col1, col2, col3 = st.columns(3)

with col1:
    lista_anos = ["Todos"] + sorted(df_melted["Ano"].dropna().unique().tolist())
    ano = st.selectbox("Ano", lista_anos)

with col2:
    lista_meses = ["Todos"] + sorted(df_melted["Mes"].dropna().unique().tolist())
    mes = st.selectbox("Mês", lista_meses)

with col3:
    ministerio = st.selectbox(
        "Ministério",
        ["Todos"] + sorted(df_melted["Ministerio"].dropna().unique().tolist())
    )

nome = st.text_input("🔎 Buscar nome")

# Aplicar filtros
df_filtrado = df_melted.copy()

if ano != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Ano"] == ano]

if mes != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Mes"] == mes]

if ministerio != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Ministerio"] == ministerio]

if nome:
    df_filtrado = df_filtrado[df_filtrado["Nome"].str.contains(nome, case=False, na=False)]

df_filtrado = df_filtrado.sort_values(by="Data")

# =============================
# TABELA DETALHADA COM CORES (mantendo como estava)
# =============================
st.subheader("📋 Escalas (detalhado)")

df_exib = df_filtrado[["Data", "Nome", "Ministerio"]].copy()
df_exib["Data"] = df_exib["Data"].dt.strftime("%d/%m/%Y")

safe_dataframe(
    criar_styler(df_exib),
    use_container_width=True
)

# =============================
# CONTAGEM (mantendo)
# =============================
st.subheader("📊 Quantas vezes cada pessoa atuou (no filtro atual)")

contagem = (
    df_filtrado.groupby("Nome")
    .size()
    .reset_index(name="Quantidade")
    .sort_values("Quantidade", ascending=False)
)

safe_dataframe(contagem, hide_index=True, use_container_width=True)

if not contagem.empty:
    st.bar_chart(contagem.set_index("Nome"))

# =============================
# AGENDA INDIVIDUAL (mantendo)
# =============================
if nome:
    st.subheader(f"📆 Agenda completa de {nome}")

    agenda = df_melted[df_melted["Nome"].str.contains(nome, case=False, na=False)].sort_values(by="Data")
    agenda_exib = agenda[["Data", "Nome", "Ministerio"]].copy()
    agenda_exib["Data"] = agenda_exib["Data"].dt.strftime("%d/%m/%Y")

    safe_dataframe(
        criar_styler(agenda_exib),
        use_container_width=True
    )
