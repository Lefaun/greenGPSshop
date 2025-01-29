import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
import folium
from streamlit_folium import st_folium
from sklearn.preprocessing import MinMaxScaler

# === Simulação de Usuários Cadastrados ===
USUARIOS = {"admin": "1234", "usuario": "senha123"}

# === Função de Login ===
def login():
    st.sidebar.title("🔑 Login")
    username = st.sidebar.text_input("Usuário")
    password = st.sidebar.text_input("Senha", type="password")

    if st.sidebar.button("Entrar"):
        if username in USUARIOS and USUARIOS[username] == password:
            st.session_state["logado"] = True
            st.session_state["usuario"] = username
            st.session_state["carrinho"] = {}
            st.sidebar.success(f"Bem-vindo, {username}!")
        else:
            st.sidebar.error("Usuário ou senha incorretos!")

# === Verifica Login ===
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    login()
    st.stop()

# === Criando abas ===
aba = st.sidebar.radio("Escolha uma opção:", ["🛍️ Loja Sustentável", "🗺️ Planejar Rota"])

# === Funções para Planejador de Rotas ===
def carregar_e_processar_dados(file):
    df = pd.read_csv(file)
    scaler = MinMaxScaler()
    df[['poluicao_norm', 'transito_norm']] = scaler.fit_transform(df[['poluicao', 'transito']])
    df['score'] = (df['poluicao_norm'] + df['transito_norm']) / 2
    return df

def encontrar_rota_otimizada(df, ponto_inicial, ponto_final):
    G = nx.Graph()
    for _, row in df.iterrows():
        G.add_node(row.name, pos=(row['latitude'], row['longitude']), score=row['score'])

    for i, row1 in df.iterrows():
        for j, row2 in df.iterrows():
            if i != j:
                dist = np.linalg.norm([row1['latitude'] - row2['latitude'], row1['longitude'] - row2['longitude']])
                peso = dist + (row1['score'] + row2['score'])  
                G.add_edge(i, j, weight=peso)

    caminho = nx.shortest_path(G, source=ponto_inicial, target=ponto_final, weight='weight')
    return df.loc[caminho]

def criar_mapa(df_rota):
    centro = [df_rota['latitude'].mean(), df_rota['longitude'].mean()]
    m = folium.Map(location=centro, zoom_start=13)

    for _, row in df_rota.iterrows():
        folium.Marker(
            [row['latitude'], row['longitude']],
            popup=f"Poluição: {row['poluicao']:.2f} | Trânsito: {row['transito']:.2f}"
        ).add_to(m)

    pontos = df_rota[['latitude', 'longitude']].values.tolist()
    folium.PolyLine(pontos, color='blue', weight=2.5, opacity=0.7).add_to(m)
    return m

if aba == "🗺️ Planejar Rota":
    st.title("🗺️ Planejador de Rota Ecológica")
    uploaded_file = st.file_uploader("📂 Escolha um arquivo CSV", type="csv")

    if uploaded_file:
        df = carregar_e_processar_dados(uploaded_file)
        pontos_disponiveis = df.index.tolist()
        
        ponto_inicial = st.selectbox("Selecione o Ponto Inicial", pontos_disponiveis)
        ponto_final = st.selectbox("Selecione o Ponto Final", pontos_disponiveis)

        if st.button("🔍 Calcular Melhor Rota"):
            df_rota = encontrar_rota_otimizada(df, ponto_inicial, ponto_final)
            mapa = criar_mapa(df_rota)
            st_folium(mapa, width=800)

# === Loja Sustentável ===
if aba == "🛍️ Loja Sustentável":
    st.title("🛍️ Loja Sustentável")
    produtos = [
        {"nome": "Cesta Orgânica", "preco": 12.99, "img": "https://via.placeholder.com/150"},
        {"nome": "Sabonete Natural", "preco": 7.50, "img": "https://via.placeholder.com/150"},
        {"nome": "Bolsa Ecológica", "preco": 15.00, "img": "https://via.placeholder.com/150"},
        {"nome": "Kit Bambu", "preco": 9.99, "img": "https://via.placeholder.com/150"},
        {"nome": "Mel Orgânico", "preco": 18.50, "img": "https://via.placeholder.com/150"},
        {"nome": "Horta Caseira", "preco": 25.00, "img": "https://via.placeholder.com/150"},
        {"nome": "Cosméticos Naturais", "preco": 19.99, "img": "https://via.placeholder.com/150"},
        {"nome": "Chá Artesanal", "preco": 10.99, "img": "https://via.placeholder.com/150"},
        {"nome": "Velas Ecológicas", "preco": 14.50, "img": "https://via.placeholder.com/150"},
    ]

    def adicionar_ao_carrinho(produto):
        if produto in st.session_state["carrinho"]:
            st.session_state["carrinho"][produto] += 1
        else:
            st.session_state["carrinho"][produto] = 1

    cols = st.columns(3)

    for i, produto in enumerate(produtos):
        with cols[i % 3]:
            st.image(produto["img"], caption=produto["nome"])
            st.write(f"💲 {produto['preco']:.2f}")
            if st.button(f"🛒 Adicionar {produto['nome']}", key=produto["nome"]):
                adicionar_ao_carrinho(produto["nome"])
                st.success(f"{produto['nome']} adicionado ao carrinho!")

    st.sidebar.title("🛒 Carrinho de Compras")
    if st.session_state["carrinho"]:
        total = 0
        for item, qtd in st.session_state["carrinho"].items():
            preco = next(p["preco"] for p in produtos if p["nome"] == item)
            subtotal = preco * qtd
            total += subtotal
            st.sidebar.write(f"{item} ({qtd}x) - 💲{subtotal:.2f}")

        st.sidebar.write(f"**Total: 💲{total:.2f}**")
        if st.sidebar.button("✅ Finalizar Pedido"):
            st.sidebar.success("Pedido realizado com sucesso! 🌱")
            st.session_state["carrinho"] = {}
    else:
        st.sidebar.write("Seu carrinho está vazio.")
