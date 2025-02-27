import streamlit as st
from streamlit_folium import st_folium
import pandas as pd
import altair as alt
from utils import calcular_emissao, obter_rotas, geocode_address, create_map, calcular_combustivel_diesel, calcular_custo_combustivel
import sidebars.analise as analise
import sidebars.calcular as calcular
import sidebars.inicio as inicio


# Seleção da página (sidebar principal)
st.sidebar.image("./assets/topsid.png", use_container_width=True)
page = st.sidebar.selectbox("Escolha uma página", ["Início", "Cálculo de Emissões", "Analises"])


# Redirecionamento para a página escolhida
if page == "Início":
    inicio.app()
elif page == "Cálculo de Emissões":
    calcular.app()
elif page == "Analises":
    analise.app()

    