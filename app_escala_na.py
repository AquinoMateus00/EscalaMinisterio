import pandas as pd
import streamlit as st

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="Escala de Ministérios", layout="wide")

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
    df = pd.read_csv(url, header=1)
    df.columns = df.columns.str.strip()

    # Converter Data
    df["Data"] = pd.to_datetime(df["Data"], dayfirst=True, errors="coerce")

    # Colunas de ministérios = tudo menos "Data"
    ministerios_cols = [c for c in df.columns if c != "Data"]

    # Transformar "wide" -> "long"
    melted = df.melt(
        id_vars=["Data"],
        value_vars=ministerios_cols,
        var_name="Ministerio",
        value_name="Nome",
    )

    # Remover vazios
    melted = melted.dropna(subset=["Nome"])

    # Suportar múltiplos nomes por célula: " e " e "," (e também ";" por segurança)
    melted["Nome"] = melted["Nome"].astype(str)
    melted["Nome"] = melted["Nome"].str.replace(" e ", ",", regex=False)
    melted["Nome"] = melted["Nome"].str.replace(";", ",", regex=False)
    melted["Nome"] = melted["Nome"].str.split(",")
    melted = melted.explode("Nome")
    melted["Nome"] = melted["Nome"].str.strip()
    melted = melted[melted["Nome"] != ""]
    melted["Nome"] = melted["Nome"].str.title()

    # Ano e mês
    melted["Ano"] = melted["Data"].dt.year
    melted["Mes"] = melted["Data"].dt.month

    return melted

df_melted = carregar_dados(csv_url)

# =============================
# CORES POR MINISTÉRIO
# =============================
MINISTERIO_CORES = {
    "Animação": "#E3F2FD",
    "Condução": "#E8F5E9",
    "Dança": "#FCE4EC",
    "Pregação": "#FFF3E0",
    "Comunicação": "#F3E5F5",
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

    # Esconder índice
    try:
        styler = styler.hide(axis="index")
    except Exception:
        styler = styler.hide_index()

    return styler

# =============================
# FUNÇÕES DE "GRUPOS" (por Data)
# =============================
def montar_grupos_por_data(df: pd.DataFrame) -> pd.DataFrame:
    # Agrupa por Data e junta Ministérios e Servos (sem repetir)
    grupos = (
        df.groupby("Data")
        .agg(
            Ministerios=("Ministerio", lambda s: " | ".join(sorted(set(map(str, s))))),
            Servos=("Nome", lambda s: ", ".join(sorted(set(map(str, s)))))
        )
        .reset_index()
        .sort_values("Data")
    )
    # Data no formato BR para exibição
    grupos["Data"] = grupos["Data"].dt.strftime("%d/%m/%Y")
    return grupos

def filtrar_grupos(grupos_df: pd.DataFrame, df_original: pd.DataFrame):
    """
    grupos_df tem Data como string formatada.
    df_original tem Data como datetime.
    Vamos usar df_original pra comparar datas e depois mapear para grupos_df.
    """
    # Datas únicas ordenadas (datetime)
    datas_ordenadas = sorted(df_original["Data"].dropna().dt.normalize().unique())

    hoje = pd.Timestamp.today().normalize()

    proximas = [d for d in datas_ordenadas if d >= hoje]
    passadas = [d for d in datas_ordenadas if d < hoje]

    # Converte datetime -> string dd/mm/yyyy para filtrar em grupos_df
    prox_str = [pd.to_datetime(d).strftime("%d/%m/%Y") for d in proximas]
    past_str = [pd.to_datetime(d).strftime("%d/%m/%Y") for d in passadas]

    proximo_grupo = grupos_df[grupos_df["Data"].isin(prox_str[:1])]
    proximos_3 = grupos_df[grupos_df["Data"].isin(prox_str[:3])]
    ultimos_5 = grupos_df[grupos_df["Data"].isin(past_str[-5:])]

    return proximo_grupo, proximos_3, ultimos_5

# =============================
# UI
# =============================
st.title("📅 Escala de Ministérios")

# Legenda
with st.expander("🎨 Legenda de cores por ministério", expanded=False):
    cols = st.columns(3)
    items = list(MINISTERIO_CORES.items())
    for i, (m, cor) in enumerate(items):
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
# TELA INICIAL: PRÓXIMOS / ÚLTIMOS GRUPOS
# =============================
grupos = montar_grupos_por_data(df_melted)
proximo_grupo, proximos_3, ultimos_5 = filtrar_grupos(grupos, df_melted)

st.subheader("➡️ Próximo Grupo")
if proximo_grupo.empty:
    st.info("Não encontrei grupos futuros a partir de hoje.")
else:
    st.dataframe(proximo_grupo[["Data", "Ministerios", "Servos"]], hide_index=True, use_container_width=True)

st.subheader("⏭️ Próximos 3 Grupos")
if proximos_3.empty:
    st.info("Não encontrei próximos grupos a partir de hoje.")
else:
    st.dataframe(proximos_3[["Data", "Ministerios", "Servos"]], hide_index=True, use_container_width=True)

st.subheader("⬅️ Últimos 5 Grupos")
if ultimos_5.empty:
    st.info("Não encontrei grupos anteriores a hoje.")
else:
    st.dataframe(ultimos_5[["Data", "Ministerios", "Servos"]], hide_index=True, use_container_width=True)

st.divider()

# =============================
# FILTROS (com "Todos")
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
# TABELA DETALHADA COM CORES
# =============================
st.subheader("📋 Escalas (detalhado)")

df_exib = df_filtrado[["Data", "Nome", "Ministerio"]].copy()
df_exib["Data"] = df_exib["Data"].dt.strftime("%d/%m/%Y")

st.dataframe(
    criar_styler(df_exib),
    use_container_width=True
)

# =============================
# CONTAGEM
# =============================
st.subheader("📊 Quantas vezes cada pessoa atuou (no filtro atual)")

contagem = df_filtrado.groupby("Nome").size().reset_index(name="Quantidade").sort_values("Quantidade", ascending=False)
st.dataframe(contagem, hide_index=True, use_container_width=True)

if not contagem.empty:
    st.bar_chart(contagem.set_index("Nome"))

# =============================
# AGENDA INDIVIDUAL
# =============================
if nome:
    st.subheader(f"📆 Agenda completa de {nome}")
    agenda = df_melted[df_melted["Nome"].str.contains(nome, case=False, na=False)].sort_values(by="Data")
    agenda_exib = agenda[["Data", "Nome", "Ministerio"]].copy()
    agenda_exib["Data"] = agenda_exib["Data"].dt.strftime("%d/%m/%Y")

    st.dataframe(
        criar_styler(agenda_exib),
        use_container_width=True
    )
