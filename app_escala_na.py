import pandas as pd
import streamlit as st

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(
    page_title="Escala de Ministérios",
    page_icon="📅",
    layout="wide"
)

# =========================================================
# CSS
# =========================================================
st.markdown("""
<style>

.main {
    padding-top: 1rem;
}

.block-container {
    padding-top: 1rem;
}

.card {
    border: 1px solid #31333F;
    border-radius: 16px;
    padding: 18px;
    margin-bottom: 15px;
    background-color: #0E1117;
}

.ministerio {
    font-size: 1.4rem;
    font-weight: bold;
    margin-bottom: 10px;
}

.nome {
    font-size: 1.05rem;
    margin-left: 10px;
    margin-bottom: 5px;
}

.data-box {
    background: linear-gradient(90deg, #1f2937, #111827);
    padding: 20px;
    border-radius: 18px;
    margin-bottom: 20px;
    border: 1px solid #374151;
}

@media (max-width: 768px) {

    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    h1 {
        font-size: 1.6rem !important;
    }
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# CSV URL
# =========================================================
csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTtu-b1fJg3AaYjKpcmYvdB1AaZpWGTRPr76mBxyBczreE69_A_3_NLJ4OPuGMtefWyTzl56G0oklFo/pub?output=csv"

# =========================================================
# LOAD DATA
# =========================================================
@st.cache_data(ttl=300)
def carregar_dados():

    df = pd.read_csv(csv_url, header=1)

    df.columns = df.columns.str.strip()

    df.rename(columns={"Data": "data"}, inplace=True)

    df["data"] = pd.to_datetime(
        df["data"],
        dayfirst=True,
        errors="coerce"
    )

    df = df.dropna(subset=["data"])

    ministerios_cols = [c for c in df.columns if c != "data"]

    melted = df.melt(
        id_vars=["data"],
        value_vars=ministerios_cols,
        var_name="ministerio",
        value_name="nome"
    )

    melted = melted.dropna(subset=["nome"])

    melted["nome"] = melted["nome"].astype(str)

    melted["nome"] = melted["nome"].str.replace(
        r"\s+[eE]\s+",
        ",",
        regex=True
    )

    melted["nome"] = melted["nome"].str.replace(";", ",", regex=False)

    melted["nome"] = melted["nome"].str.split(",")
    melted = melted.explode("nome")

    melted["nome"] = melted["nome"].str.strip()
    melted = melted[melted["nome"] != ""]
    melted["nome"] = melted["nome"].str.title()

    melted["ano"] = melted["data"].dt.year
    melted["mes"] = melted["data"].dt.strftime("%m")

    return melted

df = carregar_dados()

# =========================================================
# TITLE
# =========================================================
st.title("📅 Escala de Ministérios")

# =========================================================
# PRÓXIMO GRUPO
# =========================================================
st.subheader("🔥 Próximo Grupo")

hoje = pd.Timestamp.now().normalize()

proximos = df[df["data"] >= hoje].sort_values("data")

if proximos.empty:

    st.warning("Nenhum próximo grupo encontrado.")

else:

    proxima_data = proximos.iloc[0]["data"]

    grupo = proximos[proximos["data"] == proxima_data]

    st.markdown(f"""
    <div class="data-box">
        <h2>📆 {proxima_data.strftime('%d/%m/%Y')}</h2>
    </div>
    """, unsafe_allow_html=True)

    emojis = {
        "Animação": "🎵",
        "Condução": "🎤",
        "Dança": "💃",
        "Pregação": "🔨",
        "Comunicação": "📸",
        "Música": "🎸"
    }

    ordem = [
        "Animação",
        "Condução",
        "Dança",
        "Pregação",
        "Comunicação",
        "Música"
    ]

    cols = st.columns(2)

    idx = 0

    for ministerio in ordem:

        sub = grupo[grupo["ministerio"] == ministerio]

        emoji = emojis.get(ministerio, "✨")

        # 🔥 AQUI FOI O AJUSTE
        if sub.empty:
            nomes = ["Sem escala"]
        else:
            nomes = sorted(sub["nome"].dropna().unique())

        with cols[idx % 2]:

            st.markdown(f"""
            <div class="card">

            <div class="ministerio">
            {emoji} {ministerio}
            </div>
            """, unsafe_allow_html=True)

            for nome in nomes:

                if nome == "Sem escala":
                    st.markdown(
                        f"<div class='nome' style='color:#F87171;'>• {nome}</div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"<div class='nome'>• {nome}</div>",
                        unsafe_allow_html=True
                    )

            st.markdown("</div>", unsafe_allow_html=True)

        idx += 1

# =========================================================
# FILTROS
# =========================================================
st.divider()
st.subheader("🔎 Filtros")

col1, col2, col3 = st.columns(3)

with col1:
    ano = st.selectbox(
        "Ano",
        ["Todos"] + sorted(df["ano"].unique().tolist())
    )

with col2:
    mes = st.selectbox(
        "Mês",
        ["Todos"] + sorted(df["mes"].unique().tolist())
    )

with col3:
    ministerio = st.selectbox(
        "Ministério",
        ["Todos"] + sorted(df["ministerio"].unique().tolist())
    )

nome = st.text_input("Buscar nome")

# =========================================================
# FILTRAR
# =========================================================
df_filtrado = df.copy()

if ano != "Todos":
    df_filtrado = df_filtrado[df_filtrado["ano"] == ano]

if mes != "Todos":
    df_filtrado = df_filtrado[df_filtrado["mes"] == mes]

if ministerio != "Todos":
    df_filtrado = df_filtrado[df_filtrado["ministerio"] == ministerio]

if nome:
    df_filtrado = df_filtrado[
        df_filtrado["nome"].str.contains(nome, case=False, na=False)
    ]

# =========================================================
# TABELA
# =========================================================
st.divider()
st.subheader("📋 Escalas")

df_exib = df_filtrado[["data", "nome", "ministerio"]].copy()

df_exib["data"] = df_exib["data"].dt.strftime("%d/%m/%Y")

df_exib.columns = ["Data", "Nome", "Ministério"]

st.dataframe(
    df_exib,
    use_container_width=True,
    hide_index=True
)

# =========================================================
# CONTAGEM
# =========================================================
st.divider()
st.subheader("📊 Participações")

contagem = (
    df_filtrado
    .groupby("nome")
    .size()
    .reset_index(name="Quantidade")
    .sort_values("Quantidade", ascending=False)
)

contagem.columns = ["Nome", "Quantidade"]

col1, col2 = st.columns([1, 2])

with col1:
    st.dataframe(
        contagem,
        use_container_width=True,
        hide_index=True
    )

with col2:
    if not contagem.empty:
        st.bar_chart(
            data=contagem,
            x="Nome",
            y="Quantidade"
        )

# =========================================================
# AGENDA INDIVIDUAL
# =========================================================
if nome:

    st.divider()
    st.subheader(f"📆 Agenda de {nome}")

    agenda = df[df["nome"].str.contains(nome, case=False, na=False)].sort_values("data")

    agenda_exib = agenda[["data", "nome", "ministerio"]].copy()

    agenda_exib["data"] = agenda_exib["data"].dt.strftime("%d/%m/%Y")

    agenda_exib.columns = ["Data", "Nome", "Ministério"]

    st.dataframe(
        agenda_exib,
        use_container_width=True,
        hide_index=True
    )
    
