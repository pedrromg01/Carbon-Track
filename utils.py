import os
from turtle import st
import requests
import folium
import polyline
import pandas as pd
import altair as alt
import locale
from streamlit_folium import st_folium
from dotenv import load_dotenv

load_dotenv()

# Configurar o locale para o padrão brasileiro
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Chave da API do Google Maps
google_maps_key = os.getenv("GOOGLE_MAPS_API_KEY")

# Função para formatar números no padrão brasileiro
def formatar_numero_br(valor):
    """
    Formata o número no padrão brasileiro (ex: 12.345,67).
    """
    return locale.format_string('%.2f', valor, grouping=True)

# Função para obter rotas usando a API do Google Maps
def obter_rotas(origem, destino, chave_api):
    url = f'https://maps.googleapis.com/maps/api/directions/json?origin={origem}&destination={destino}&key={chave_api}&alternatives=true'
    response = requests.get(url).json()

    if response['status'] == 'OK':
        rotas = []
        for rota in response['routes']:
            distancia = rota['legs'][0]['distance']['value'] / 1000  # Convertendo para km
            tempo_total_segundos = rota['legs'][0]['duration']['value']
            horas = tempo_total_segundos // 3600
            minutos = (tempo_total_segundos % 3600) // 60
            tempo_formatado = f"{int(horas)} Horas e {int(minutos)} minutos"

            rotas.append({
                'distancia': distancia,
                'tempo': tempo_formatado,
                'overview_polyline': rota['overview_polyline']['points']
            })

        # Garantir que sempre haja 3 rotas
        while len(rotas) < 3:
            rotas.append(rotas[-1])  # Duplicar a última rota, se necessário

        return rotas
    else:
        return []

# Função para geocodificar um endereço (converter endereço em coordenadas)
def geocode_address(address):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={google_maps_key}"
    response = requests.get(url).json()
    return response['results'][0]['geometry']['location'] if response['status'] == 'OK' else None

# Função para criar um mapa interativo
def create_map(origem_coords, destino_coords, polyline_coords):
    mapa = folium.Map(location=[origem_coords['lat'], origem_coords['lng']], zoom_start=12)
    folium.Marker([origem_coords['lat'], origem_coords['lng']], popup='Origem').add_to(mapa)
    folium.Marker([destino_coords['lat'], destino_coords['lng']], popup='Destino').add_to(mapa)
    folium.PolyLine(locations=polyline.decode(polyline_coords), color="Blue", weight=2.5, opacity=1).add_to(mapa)
    return mapa

# Cálculos de Consumo
# Diesel
def calcular_combustivel_diesel(distancia_km, peso_toneladas, consumo_base=3):
    fator_ajuste = 1 + (peso_toneladas * 0.05)  # Aumento de 5% por tonelada
    consumo_total = (distancia_km / consumo_base) * fator_ajuste
    return round(consumo_total, 2)

# Híbrido
def calcular_combustivel_hibrido(distancia_km, peso_toneladas, consumo_base=6, fator_eletrico=0.2):
    fator_ajuste = 1 + (peso_toneladas * 0.05)  # Aumento de 5% por tonelada
    consumo_ajustado = consumo_base * (1 - fator_eletrico)  # Aplicando o fator elétrico
    consumo_total = (distancia_km / consumo_ajustado) * fator_ajuste
    return round(consumo_total, 2)

# Elétrico
def calcular_energia_eletrica(distancia_km, peso_toneladas, consumo_base_kwh=1):
    fator_ajuste = 1 + (peso_toneladas * 0.05)  # Aumento de 5% por tonelada
    energia_total = distancia_km * consumo_base_kwh * fator_ajuste
    return round(energia_total, 2)

# Cálculo de Custo
# Diesel
def calcular_custo_combustivel(distancia_km, peso_toneladas, preco_diesel, consumo_base=3):
    quantidade_combustivel = calcular_combustivel_diesel(distancia_km, peso_toneladas, consumo_base)
    return round(quantidade_combustivel * preco_diesel, 2)

# Híbrido
def calcular_custo_combustivel_hibrido(distancia_km, peso_toneladas, preco_combustivel, consumo_base=6):
    consumo_hibrido = calcular_combustivel_hibrido(distancia_km, peso_toneladas, consumo_base)
    return round(consumo_hibrido * preco_combustivel, 2)

# Elétrico
def calcular_custo_eletrico(distancia_km, peso_toneladas, preco_energia=0.75, consumo_base_kwh=1):
    consumo_eletrico = calcular_energia_eletrica(distancia_km, peso_toneladas, consumo_base_kwh)
    return round(consumo_eletrico * preco_energia, 2)

# Cálculos de Emissão de CO2
# Diesel
def calcular_emissao(distancia_km, peso_toneladas, consumo_base=3, coeficiente_emissao=2.7):
    consumo_total = calcular_combustivel_diesel(distancia_km, peso_toneladas, consumo_base)
    return round(consumo_total * coeficiente_emissao, 2)

# Híbrido
def calcular_emissao_hibrido(distancia_km, peso_toneladas, consumo_base=6, fator_eletrico=0.2, coeficiente_emissao=2.7):
    consumo_total = calcular_combustivel_hibrido(distancia_km, peso_toneladas, consumo_base, fator_eletrico)
    return round(consumo_total * coeficiente_emissao, 2)

# Elétrico
def calcular_emissao_eletrico(distancia_km, peso_toneladas, consumo_base_kwh=1, coeficiente_emissao_kwh=0.1):
    energia_total = calcular_energia_eletrica(distancia_km, peso_toneladas, consumo_base_kwh)
    return round(energia_total * coeficiente_emissao_kwh, 2)

# Salvar dados
def salvar_dados_em_csv(dados_rotas, origem, destino, peso, input_preco):
    # Adicionar origem, destino, peso e preço do diesel a cada rota
    for rota_data in dados_rotas:
        rota_data['Origem'] = origem
        rota_data['Destino'] = destino
        rota_data['Peso (Ton)'] = peso
        rota_data['Preço do Diesel (R$)'] = input_preco

        rota_data['Emissão de CO2 Diesel (kg)'] = calcular_emissao(rota_data['Distância (km)'], peso)
        rota_data['Emissão de CO2 Híbrido (kg)'] = calcular_emissao_hibrido(rota_data['Distância (km)'], peso)
        rota_data['Emissão de CO2 Elétrico (kg)'] = calcular_emissao_eletrico(rota_data['Distância (km)'], peso)
        rota_data['Consumo Diesel (litros)'] = calcular_combustivel_diesel(rota_data['Distância (km)'], peso)
        rota_data['Consumo Híbrido (litros)'] = calcular_combustivel_hibrido(rota_data['Distância (km)'], peso)
        rota_data['Consumo Elétrico (kWh)'] = calcular_energia_eletrica(rota_data['Distância (km)'], peso)
        rota_data['Custo do Combustível Híbrido (R$)'] = calcular_custo_combustivel_hibrido(rota_data['Distância (km)'], peso, input_preco)
        rota_data['Custo do Combustível Elétrico (R$)'] = calcular_custo_eletrico(rota_data['Distância (km)'], peso)
        rota_data['Custo do Combustível Diesel (R$)'] = calcular_custo_combustivel(rota_data['Distância (km)'], peso, input_preco)

    colunas = [
        "Rota", "Origem", "Destino", "Distância (km)", "Tempo (h)", "Preço do Diesel (R$)", "Peso (Ton)",
        "Emissão de CO2 Diesel (Kg)", "Emissão de CO2 Híbrido (kg)", "Emissão de CO2 Elétrico (kg)",
        "Consumo Diesel (litros)", "Consumo Híbrido (litros)", "Consumo Elétrico (kWh)",
        "Custo do Combustível Diesel (R$)", "Custo do Combustível Híbrido (R$)", "Custo do Combustível Elétrico (R$)"
    ]

    df = pd.DataFrame(dados_rotas, columns=colunas)

    for col in df.columns:
        if df[col].dtype in ['float64', 'int64']:  # Verificar se a coluna é numérica
            df[col] = df[col].apply(lambda x: formatar_numero_br(x))

    if not os.path.exists('dados_rotas.csv'):
        df.to_csv('dados_rotas.csv', mode='w', header=True, index=False, sep=',', decimal=',', encoding='utf-8')
    else:
        df.to_csv('dados_rotas.csv', mode='a', header=False, index=False, sep=',', decimal=',', encoding='utf-8')

    return "Dados salvos com sucesso"

# Carregar dados do CSV
def carregar_dados_do_csv():
    try:
        # Tentar carregar os dados existentes do CSV
        df = pd.read_csv('dados_rotas.csv')
        return df
    except FileNotFoundError:
        # Se o arquivo não existir, retornar um DataFrame vazio
        return pd.DataFrame(columns=["Rota", "Origem", "Destino", "Distância (km)", "Tempo (h)", "Preço do Diesel (R$)", "Peso (Ton)", "Emissão de CO2 Diesel (Kg)", "Emissão de CO2 Híbrido (kg)", "Emissão de CO2 Elétrico (kg)", "Consumo Diesel (litros)", "Consumo Híbrido (litros)", "Consumo Elétrico (kWh)", "Custo do Combustível Diesel (R$)", "Custo do Combustível Híbrido (R$)", "Custo do Combustível Elétrico (R$)"])
