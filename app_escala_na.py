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
# CSS (visual simples e responsivo)
# =========================================================
st.markdown("""
<style>
.card {
    border: 1px solid #31333F;
    border-radius: 16px;
    padding: 18px;
    margin-bottom: 15px;
    background-color: #0E1117;
}
.ministerio {
    font-size: 1.3rem;
    font-weight: bold;
    margin-bottom: 10px;
}
.nome {
    font-size: 1.05rem;
    margin-left: 10px;
    margin-bottom: 6px;
}
.data-box {
    background: linear-gradient(90deg, #1f2937, #111827);
    padding: 16px 18px;
    border-radius: 18px;
    margin-bottom: 16px;
    border: 1px solid #374151;
}
@media (max-width: 768px) {
    .block-container { padding-left: 1rem; padding-right: 1rem; }
    h1 { font-size: 1.6rem !important; }
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# CONSTANTES
# =========================================================
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTtu-b1fJg3AaYjKpcmYvdB1AaZpWGTRPr76mBxyBczreE69_A_3_NLJ4OPuGMtefWyTzl56G0oklFo/pub?output=csv"

MESES = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

EMOJIS = {
    "Animação": "🎵",
    "Condução": "🎤",
    "Dança": "💃",
    "Pregação": "🔨",
    "Comunicação": "📸",
    "Música": "🎸"
}

ORDEM_PADRAO = ["Animação", "Condução", "Dança", "Pregação", "Comunicação", "Música"]

def ordenar_ministerios(cols_encontradas):
    """Mantém ordem padrão e adiciona qualquer outro ministério existente na planilha."""
    cols = []
    for m in ORDEM_PADRAO:
        if m in cols_encontradas:
            cols.append(m)
    extras = [c for c in cols_encontradas if c not in cols]
    return cols + extras

# =========================================================
# LOAD DATA (raw = formato original / long = para filtros e contagem)
# =========================================================
@st.cache_data(ttl=60)
def carregar_dados(url: str):
    df_raw = pd.read_csv(url, header=1)
    df_raw.columns = df_raw.columns.str.strip()

    # renomeia coluna de data para "data"
    if "Data" in df_raw.columns:
        df_raw = df_raw.rename(columns={"Data": "data"})

    df_raw["data"] = pd.to_datetime(df_raw["data"], dayfirst=True, errors="coerce")
    df_raw = df_raw.dropna(subset=["data"]).copy()

    ministerios_cols = [c for c in df_raw.columns if c != "data"]
    ministerios_cols = ordenar_ministerios(ministerios_cols)

    # LONG: explode nomes para contagem e busca
    df_long = df_raw.melt(
        id_vars=["data"],
        value_vars=ministerios_cols,
        var_name="ministerio",
        value_name="nome"
    )

    df_long = df_long.dropna(subset=["nome"]).copy()
    df_long["nome"] = df_long["nome"].astype(str)

    # separadores: " e ", "," e ";"
    df_long["nome"] = df_long["nome"].str.replace(r"\s+[eE]\s+", ",", regex=True)
    df_long["nome"] = df_long["nome"].str.replace(";", ",", regex=False)
    df_long["nome"] = df_long["nome"].str.split(",")
    df_long = df_long.explode("nome")

    df_long["nome"] = df_long["nome"].str.strip()
    df_long = df_long[df_long["nome"] != ""]
    df_long["nome"] = df_long["nome"].str.title()

    df_long["ano"] = df_long["data"].dt.year
    df_long["mes"] = df_long["data"].dt.month

    return df_raw, df_long, ministerios_cols

df_raw, df_long, ministerios_cols = carregar_dados(CSV_URL)

# =========================================================
# SIDEBAR - MENU + FILTROS
# =========================================================
st.sidebar.title("📋 Menu")

pagina = st.sidebar.radio(
    "Ir para:",
    ["🔥 Escala", "🗂️ Tabela Original", "📊 Participações"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.subheader("🔎 Filtros")

# Ano (padrão 2026)
anos = sorted(df_long["ano"].dropna().unique().tolist())
idx_ano = anos.index(2026) if 2026 in anos else 0
ano = st.sidebar.selectbox("Ano", anos, index=idx_ano)

# Mês (Mostra nome, mas retorna número) usando format_func [1](https://docs.streamlit.io/develop/api-reference/widgets/st.selectbox)
meses_disponiveis = sorted(df_long[df_long["ano"] == ano]["mes"].dropna().unique().tolist())
opcoes_mes = [0] + meses_disponiveis  # 0 = "Todos"
mes_num = st.sidebar.selectbox(
    "Mês",
    opcoes_mes,
    index=0,
    format_func=lambda x: "Todos" if x == 0 else MESES.get(x, str(x))
)

# Data (opcional) - aparece sempre na lateral e pode ficar vazia (None) [2](https://docs.streamlit.io/develop/api-reference/widgets/st.date_input)
data_escolhida = st.sidebar.date_input(
    "Data (opcional)",
    value=None,              # permite vazio
    format="DD/MM/YYYY"      # mostra no formato BR
)

# Ministério
ministerio = st.sidebar.selectbox(
    "Ministério",
    ["Todos"] + ordenar_ministerios(sorted(df_long["ministerio"].unique().tolist())),
    index=0
)

# Nome
nome = st.sidebar.text_input("Nome (opcional)")

# =========================================================
# APLICAR FILTROS (no LONG)
# =========================================================
df_f = df_long[df_long["ano"] == ano].copy()

if mes_num != 0:
    df_f = df_f[df_f["mes"] == mes_num]

if data_escolhida is not None:
    df_f = df_f[df_f["data"].dt.date == data_escolhida]

if ministerio != "Todos":
    df_f = df_f[df_f["ministerio"] == ministerio]

if nome:
    df_f = df_f[df_f["nome"].str.contains(nome, case=False, na=False)]

# =========================================================
# TITULO
# =========================================================
st.title("📅 Escala de Ministérios")

# =========================================================
# PAGINA: ESCALA
# =========================================================
if pagina == "🔥 Escala":

    st.header("🔥 Escala do Grupo")

    tipo = st.selectbox(
        "Mostrar:",
        ["Próximo Grupo", "Próximos", "Anteriores"],
        index=0
    )

    qtd = 1
    if tipo in ["Próximos", "Anteriores"]:
        qtd = st.number_input("Quantidade de grupos", min_value=1, max_value=20, value=3, step=1)

    hoje = pd.Timestamp.now().normalize()

    if tipo == "Próximo Grupo":
        dados = df_f[df_f["data"] >= hoje].sort_values("data")
        datas = dados["data"].drop_duplicates().head(1)

    elif tipo == "Próximos":
        dados = df_f[df_f["data"] >= hoje].sort_values("data")
        datas = dados["data"].drop_duplicates().head(int(qtd))

    else:  # Anteriores
        dados = df_f[df_f["data"] < hoje].sort_values("data", ascending=False)
        datas = dados["data"].drop_duplicates().head(int(qtd))

    if datas.empty:
        st.warning("Nenhum grupo encontrado com os filtros atuais.")
    else:
        ordem = ordenar_ministerios(ministerios_cols)

        for data in datas:
            grupo = df_f[df_f["data"] == data]

            st.markdown(f"""
            <div class="data-box">
              <h2 style="margin:0;">📆 {data.strftime('%d/%m/%Y')}</h2>
            </div>
            """, unsafe_allow_html=True)

            cols = st.columns(2)
            i = 0

            for m in ordem:
                sub = grupo[grupo["ministerio"] == m]

                # sempre mostra o ministério (mesmo vazio)
                if sub.empty:
                    nomes = ["Sem escala"]
                else:
                    nomes = sorted(sub["nome"].dropna().unique())

                with cols[i % 2]:
                    st.markdown(
                        f"<div class='card'><div class='ministerio'>{EMOJIS.get(m,'✨')} {m}</div>",
                        unsafe_allow_html=True
                    )
                    for n in nomes:
                        if n == "Sem escala":
                            st.markdown(f"<div class='nome' style='color:#F87171;'>• {n}</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div class='nome'>• {n}</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                i += 1

# =========================================================
# PAGINA: TABELA ORIGINAL
# =========================================================
elif pagina == "🗂️ Tabela Original":

    st.header("🗂️ Tabela Original (como na planilha)")

    raw_f = df_raw.copy()
    raw_f["ano"] = raw_f["data"].dt.year
    raw_f["mes"] = raw_f["data"].dt.month
    raw_f = raw_f[raw_f["ano"] == ano]

    if mes_num != 0:
        raw_f = raw_f[raw_f["mes"] == mes_num]

    if data_escolhida is not None:
        raw_f = raw_f[raw_f["data"].dt.date == data_escolhida]

    # filtro por nome no raw: procura em qualquer coluna de ministério
    if nome:
        cols_min = [c for c in raw_f.columns if c not in ["data", "ano", "mes"]]
        mask = raw_f[cols_min].apply(lambda col: col.astype(str).str.contains(nome, case=False, na=False))
        raw_f = raw_f[mask.any(axis=1)]

    cols_min = [c for c in df_raw.columns if c != "data"]
    cols_min = ordenar_ministerios(cols_min)

    exib = raw_f[["data"] + cols_min].copy()
    exib["data"] = exib["data"].dt.strftime("%d/%m/%Y")
    exib = exib.rename(columns={"data": "Data"})

    st.dataframe(exib, use_container_width=True, hide_index=True)

# =========================================================
# PAGINA: PARTICIPAÇÕES
# =========================================================
else:

    st.header("📊 Participações")

    contagem = (
        df_f.groupby("nome")
        .size()
        .reset_index(name="Quantidade")
        .sort_values("Quantidade", ascending=False)
    )

    c1, c2 = st.columns([1, 2])

    with c1:
        st.dataframe(contagem, use_container_width=True, hide_index=True)

    with c2:
        if not contagem.empty:
            st.bar_chart(data=contagem.set_index("nome"))

    if nome:
        st.divider()
        st.subheader(f"📆 Agenda de {nome}")

        agenda = df_long[
            (df_long["ano"] == ano) &
            (df_long["nome"].str.contains(nome, case=False, na=False))
        ].sort_values("data")

        agenda_exib = agenda[["data", "nome", "ministerio"]].copy()
        agenda_exib["data"] = agenda_exib["data"].dt.strftime("%d/%m/%Y")
        agenda_exib.columns = ["Data", "Nome", "Ministério"]

        st.dataframe(agenda_exib, use_container_width=True, hide_index=True)
