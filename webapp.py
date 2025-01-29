import streamlit as st
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import folium
from streamlit_folium import st_folium
import networkx as nx

# Dicionário de usuários e senhas (simples, apenas para teste)
USUARIOS = {
    "admin": "1234",
    "user1": "abcd"
}

# Função para verificar login
def autenticar(usuario, senha):
    return USUARIOS.get(usuario) == senha

# Função para carregar e processar dados
def carregar_e_processar_dados(file):
    df = pd.read_csv(file)
    scaler = MinMaxScaler()
    df[['poluicao_norm', 'transito_norm']] = scaler.fit_transform(df[['poluicao', 'transito']])
    df['score'] = (df['poluicao_norm'] + df['transito_norm']) / 2
    return df

# Função para encontrar o melhor percurso
def encontrar_melhor_circuito(df, num_pontos=10):
    melhores_pontos = df.nsmallest(num_pontos, 'score')
    G = nx.Graph()
    for idx, row in melhores_pontos.iterrows():
        G.add_node(idx, pos=(row['latitude'], row['longitude']))
    for idx1, row1 in melhores_pontos.iterrows():
        for idx2, row2 in melhores_pontos.iterrows():
            if idx1 != idx2:
                dist = np.sqrt((row1['latitude'] - row2['latitude'])**2 + 
                             (row1['longitude'] - row2['longitude'])**2)
                G.add_edge(idx1, idx2, weight=dist)
    circuito = nx.approximation.traveling_salesman_problem(G, cycle=True)
    return melhores_pontos.loc[circuito]

# Função para criar o mapa
def criar_mapa(df_circuito):
    centro = [df_circuito['latitude'].mean(), df_circuito['longitude'].mean()]
    m = folium.Map(location=centro, zoom_start=13)
    for idx, row in df_circuito.iterrows():
        folium.Marker(
            [row['latitude'], row['longitude']],
            popup=f"Poluição: {row['poluicao']:.2f}<br>Trânsito: {row['transito']:.2f}",
            tooltip=f"Ponto {idx}"
        ).add_to(m)
    pontos = df_circuito[['latitude', 'longitude']].values.tolist()
    pontos.append(pontos[0])  
    folium.PolyLine(pontos, weight=2, color='red', opacity=0.8).add_to(m)
    return m

# Interface principal
def main():
    st.title('Otimizador de Percurso Sustentável')

    # Controle de login
    if "logado" not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:
        st.subheader("🔐 Login")
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if autenticar(usuario, senha):
                st.session_state.logado = True
                st.success(f"Bem-vindo, {usuario}!")
                st.experimental_rerun()
            else:
                st.error("Usuário ou senha incorretos!")
        return

    # Se logado, exibe a aplicação
    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({"logado": False}))

    uploaded_file = st.file_uploader("Escolha seu arquivo CSV", type="csv")
    if uploaded_file is not None:
        df = carregar_e_processar_dados(uploaded_file)
        num_pontos = st.slider('Número de pontos no circuito', 5, 20, 10)
        df_circuito = encontrar_melhor_circuito(df, num_pontos)
        mapa = criar_mapa(df_circuito)
        st_folium(mapa, width=800)

        st.subheader('Estatísticas do Circuito')
        col1, col2 = st.columns(2)
        with col1:
            st.metric('Média de Poluição', f"{df_circuito['poluicao'].mean():.2f}")
        with col2:
            st.metric('Média de Trânsito', f"{df_circuito['transito'].mean():.2f}")
        st.subheader('Pontos do Circuito')
        st.dataframe(df_circuito[['latitude', 'longitude', 'poluicao', 'transito']])

if __name__ == '__main__':
    main()
