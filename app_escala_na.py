import pandas as pd
import streamlit as st

# 🔗 Link CSV
csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTtu-b1fJg3AaYjKpcmYvdB1AaZpWGTRPr76mBxyBczreE69_A_3_NLJ4OPuGMtefWyTzl56G0oklFo/pub?output=csv"

# 📥 Carregar dados
df = pd.read_csv(csv_url, header=1)

# 🧹 Limpar colunas
df.columns = df.columns.str.strip()

# 📅 Converter Data
df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')

# 🔄 Transformar estrutura
df_melted = df.melt(
    id_vars=['Data'],
    value_vars=['Animação', 'Condução', 'Dança', 'Pregação', 'Comunicação', 'Música'],
    var_name='Ministerio',
    value_name='Nome'
)

# 🗑️ Remover vazios
df_melted = df_melted.dropna(subset=['Nome'])

# 🔥 Separar múltiplos nomes
df_melted['Nome'] = df_melted['Nome'].astype(str)
df_melted['Nome'] = df_melted['Nome'].str.replace(' e ', ',', regex=False)
df_melted['Nome'] = df_melted['Nome'].str.split(',')
df_melted = df_melted.explode('Nome')
df_melted['Nome'] = df_melted['Nome'].str.strip()
df_melted = df_melted[df_melted['Nome'] != '']
df_melted['Nome'] = df_melted['Nome'].str.title()

# ➕ Ano e Mês
df_melted['Ano'] = df_melted['Data'].dt.year
df_melted['Mes'] = df_melted['Data'].dt.month

# 🎯 Título
st.title("📅 Escala de Ministérios")

# 🎛️ Filtros com "Todos"
col1, col2, col3 = st.columns(3)

with col1:
    lista_anos = ["Todos"] + sorted(df_melted['Ano'].dropna().unique())
    ano = st.selectbox("Ano", lista_anos)

with col2:
    lista_meses = ["Todos"] + sorted(df_melted['Mes'].dropna().unique())
    mes = st.selectbox("Mês", lista_meses)

with col3:
    ministerio = st.selectbox(
        "Ministério",
        ["Todos"] + sorted(df_melted['Ministerio'].dropna().unique())
    )

nome = st.text_input("🔎 Buscar nome")

# 🔎 Aplicar filtros
df_filtrado = df_melted.copy()

if ano != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Ano'] == ano]

if mes != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Mes'] == mes]

if ministerio != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Ministerio'] == ministerio]

if nome:
    df_filtrado = df_filtrado[
        df_filtrado['Nome'].str.contains(nome, case=False, na=False)
    ]

# 📅 Ordenar
df_filtrado = df_filtrado.sort_values(by='Data')

# 📅 FORMATAR DATA (DD/MM/YYYY)
df_filtrado['Data'] = df_filtrado['Data'].dt.strftime('%d/%m/%Y')

# 📊 Mostrar escala
st.subheader("📋 Escalas")
st.dataframe(df_filtrado[['Data', 'Nome', 'Ministerio']])

# 📈 Contagem
st.subheader("📊 Quantas vezes cada pessoa atuou")

contagem = df_filtrado.groupby('Nome').size().reset_index(name='Quantidade')
contagem = contagem.sort_values(by='Quantidade', ascending=False)

st.dataframe(contagem)

# 📊 Gráfico
if not contagem.empty:
    st.bar_chart(contagem.set_index('Nome'))

# 👤 Agenda individual
if nome:
    st.subheader(f"📆 Agenda de {nome}")

    agenda = df_melted[
        df_melted['Nome'].str.contains(nome, case=False, na=False)
    ].sort_values(by='Data')

    agenda['Data'] = agenda['Data'].dt.strftime('%d/%m/%Y')

    st.dataframe(agenda[['Data', 'Ministerio']])
