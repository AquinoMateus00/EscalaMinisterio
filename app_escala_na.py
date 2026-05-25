import pandas as pd
import streamlit as st

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(
    page_title="Escala de Ministérios",
    layout="wide"
)

# ==========================================
# CSS
# ==========================================
st.markdown("""
<style>

.main {
    padding-top: 1rem;
}

.block-container {
    padding-top: 1rem;
}

.card {
    background-color: #111827;
    padding: 20px;
    border-radius: 18px;
    margin-bottom: 20px;
    border: 1px solid #374151;
}

.ministerio {
    font-size: 1.2rem;
    font-weight: bold;
    margin-top: 15px;
    color: #60A5FA;
}

.nome {
    margin-left: 10px;
    font-size: 1rem;
}

.resumo-box {
    background-color: #111827;
    padding: 25px;
    border-radius: 20px;
    border: 1px solid #374151;
    margin-bottom: 20px;
}

@media (max-width: 768px) {

    .block-container {
        padding-left: 0.7rem;
        padding-right: 0.7rem;
    }

    h1 {
        font-size: 1.5rem !important;
    }
}

</style>
""", unsafe_allow_html=True)

# ==========================================
# GOOGLE SHEETS CSV
# ==========================================
csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTtu-b1fJg3AaYjKpcmYvdB1AaZpWGTRPr76mBxyBczreE69_A_3_NLJ4OPuGMtefWyTzl56G0oklFo/pub?output=csv"

# ==========================================
# LOAD DATA
# ==========================================
@st.cache_data(ttl=300)
def carregar_dados():

    df = pd.read_csv(csv_url)

    df.columns = df.columns.str.strip()

    # Converter Data
    df["Data"] = pd.to_datetime(
        df["Data"],
        dayfirst=True,
        errors="coerce"
    )

    # Todas colunas exceto data
    ministerios_cols = [
        c for c in df.columns
        if c != "Data"
    ]

    # TRANSFORMAR EM LONG FORMAT
    melted = df.melt(
        id_vars=["Data"],
        value_vars=ministerios_cols,
        var_name="Ministerio",
        value_name="Nome"
    )

    # Remover vazios
    melted = melted.dropna(subset=["Nome"])

    # Converter nomes
    melted["Nome"] = melted["Nome"].astype(str)

    melted["Nome"] = melted["Nome"].str.replace(
        r"\s+[eE]\s+",
        ",",
        regex=True
    )

    melted["Nome"] = melted["Nome"].str.replace(
        ";",
        ",",
        regex=False
    )

    # SPLIT NOMES
    melted["Nome"] = melted["Nome"].str.split(",")

    melted = melted.explode("Nome")

    melted["Nome"] = melted["Nome"].str.strip()

    melted = melted[melted["Nome"] != ""]

    # Padronizar
    melted["Nome"] = melted["Nome"].str.title()

    # Ano e mês
    melted["Ano"] = melted["Data"].dt.year
    melted["Mes"] = melted["Data"].dt.strftime("%m")

    return melted

df = carregar_dados()

# ==========================================
# TITULO
# ==========================================
st.title("📅 Escala de Ministérios")

# ==========================================
# PRÓXIMO GRUPO
# ==========================================
st.subheader("🔥 Próximo Grupo")

hoje = pd.Timestamp.now().normalize()

proximos = df[
    df["Data"] >= hoje
].sort_values("Data")

if proximos.empty:

    st.warning("Nenhum próximo grupo encontrado.")

else:

    proxima_data = proximos.iloc[0]["Data"]

    grupo = proximos[
        proximos["Data"] == proxima_data
    ]

    data_formatada = proxima_data.strftime("%d/%m/%Y")

    st.markdown(f"""
    <div class="resumo-box">
        <h2>📆 {data_formatada}</h2>
    </div>
    """, unsafe_allow_html=True)

    # EMOJIS POR MINISTÉRIO
    emojis = {
        "Dança": "💃",
        "Musica": "🎸",
        "Música": "🎸",
        "Pregação": "🔨",
        "Pregador": "🔨",
        "Comunicação": "📸",
        "Condução": "🎤",
        "Animação": "🎵"
    }

    # AGRUPAR POR MINISTÉRIO
    for ministerio, sub in grupo.groupby("Ministerio"):

        emoji = emojis.get(ministerio, "✨")

        nomes = sorted(
            sub["Nome"].dropna().unique()
        )

        html = f"""
        <div class="card">

        <div class="ministerio">
        {emoji} {ministerio}
        </div>
        """

        for nome in nomes:
            html += f"""
            <div class="nome">
            - {nome}
            </div>
            """

        html += "</div>"

        st.markdown(html, unsafe_allow_html=True)

# ==========================================
# FILTROS
# ==========================================
st.divider()

st.subheader("🔎 Filtros")

col1, col2, col3 = st.columns(3)

with col1:

    anos = ["Todos"] + sorted(
        df["Ano"].dropna().unique().tolist()
    )

    ano = st.selectbox(
        "Ano",
        anos
    )

with col2:

    meses = ["Todos"] + sorted(
        df["Mes"].dropna().unique().tolist()
    )

    mes = st.selectbox(
        "Mês",
        meses
    )

with col3:

    ministerio = st.selectbox(
        "Ministério",
        ["Todos"] + sorted(
            df["Ministerio"].dropna().unique().tolist()
        )
    )

nome = st.text_input("🔎 Buscar nome")

# ==========================================
# FILTRAR
# ==========================================
df_filtrado = df.copy()

if ano != "Todos":
    df_filtrado = df_filtrado[
        df_filtrado["Ano"] == ano
    ]

if mes != "Todos":
    df_filtrado = df_filtrado[
        df_filtrado["Mes"] == mes
    ]

if ministerio != "Todos":
    df_filtrado = df_filtrado[
        df_filtrado["Ministerio"] == ministerio
    ]

if nome:
    df_filtrado = df_filtrado[
        df_filtrado["Nome"].str.contains(
            nome,
            case=False,
            na=False
        )
    ]

# ==========================================
# TABELA
# ==========================================
st.divider()

st.subheader("📋 Escalas")

df_exib = df_filtrado[
    ["Data", "Nome", "Ministerio"]
].copy()

df_exib["Data"] = df_exib["Data"].dt.strftime("%d/%m/%Y")

st.dataframe(
    df_exib,
    use_container_width=True,
    hide_index=True
)

# ==========================================
# CONTAGEM
# ==========================================
st.divider()

st.subheader("📊 Quantas vezes cada pessoa serviu")

contagem = (
    df_filtrado
    .groupby("Nome")
    .size()
    .reset_index(name="Quantidade")
    .sort_values("Quantidade", ascending=False)
)

st.dataframe(
    contagem,
    use_container_width=True,
    hide_index=True
)

# ==========================================
# GRÁFICO
# ==========================================
if not contagem.empty:

    st.bar_chart(
        data=contagem,
        x="Nome",
        y="Quantidade"
    )

# ==========================================
# AGENDA INDIVIDUAL
# ==========================================
if nome:

    st.divider()

    st.subheader(f"📆 Agenda de {nome}")

    agenda = df[
        df["Nome"].str.contains(
            nome,
            case=False,
            na=False
        )
    ].sort_values("Data")

    agenda["Data"] = agenda["Data"].dt.strftime("%d/%m/%Y")

    st.dataframe(
        agenda[["Data", "Nome", "Ministerio"]],
        use_container_width=True,
        hide_index=True
    )
