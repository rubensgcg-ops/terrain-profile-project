import streamlit as st
import numpy as np
import requests
import io
import csv
import math
import pandas as pd
 
# =======================================
# FUNÇÕES AUXILIARES (inalteradas)
# =======================================
 
def interpolate(start, end, n=200):
    lat1, lon1 = start
    lat2, lon2 = end
    lats = np.linspace(lat1, lat2, n)
    lons = np.linspace(lon1, lon2, n)
    return list(zip(lats.tolist(), lons.tolist()))
 
def haversine(a, b):
    lat1, lon1 = a
    lat2, lon2 = b
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    x = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(x), math.sqrt(1-x))
    return R * c
 
# Função para buscar elevações (extraída da lógica anterior)
def fetch_elevations(points):
    def fetch_block(block):
        coords_str = "|".join([f"{p[0]},{p[1]}" for p in block])
        url = "api.opentopodata.org"
        r = requests.get(url, params={"locations": coords_str}, timeout=25)
        return r.json().get("results", [])
 
    BLOCK_SIZE = 100
    elevations = []
 
    for i in range(0, len(points), BLOCK_SIZE):
        block_points = points[i:i+BLOCK_SIZE]
        try:
            results = fetch_block(block_points)
            block_elev = [r.get("elevation", None) for r in results]
        except:
            # Tratamento de erro simplificado para Streamlit
            st.error("Erro ao buscar elevações para um bloco. Usando fallback...")
            block_elev = []
            for lat, lon in block_points:
                try:
                    r = requests.get(
                        "api.open-elevation.com",
                        params={"locations": f"{lat},{lon}"},
                        timeout=10
                    )
                    block_elev.append(r.json()["results"][0]["elevation"])
                except:
                    block_elev.append(None)
        elevations.extend(block_elev)
    return elevations
 
# =======================================
# INTERFACE STREAMLIT
# =======================================
 
st.title("Perfil de Elevação com Streamlit")
 
# Entradas do usuário na barra lateral
st.sidebar.header("Parâmetros do Perfil")
lat1 = st.sidebar.number_input("Latitude Inicial", value=-23.6, format="%.4f")
lon1 = st.sidebar.number_input("Longitude Inicial", value=-46.6, format="%.4f")
lat2 = st.sidebar.number_input("Latitude Final", value=-23.5, format="%.4f")
lon2 = st.sidebar.number_input("Longitude Final", value=-46.5, format="%.4f")
n    = st.sidebar.slider("Número de Pontos (n)", 50, 500, 200)
 
if st.sidebar.button("Gerar Perfil"):
    st.subheader("Processando...")
    points = interpolate((lat1, lon1), (lat2, lon2), n)
    elevations = fetch_elevations(points)
 
    distances = [0.0]
    for i in range(1, len(points)):
        distances.append(distances[-1] + haversine(points[i-1], points[i]))
 
    valid = [(i, e) for i, e in enumerate(elevations) if e is not None]
    if valid:
        max_idx, max_elev = max(valid, key=lambda x: x[1])
        st.success(f"Maior elevação encontrada: {max_elev:.2f} metros.")
    else:
        st.warning("Nenhuma elevação válida encontrada.")
        max_idx = None
        max_elev = None
 
    # Exibir resultados
    df = pd.DataFrame({
        "Latitude": [p[0] for p in points],
        "Longitude": [p[1] for p in points],
        "Elevação (m)": elevations,
        "Distância Cumulativa (m)": distances
    })
 
    st.subheader("Gráfico de Elevação vs Distância")
    st.line_chart(df, x="Distância Cumulativa (m)", y="Elevação (m)")
    st.subheader("Dados em Tabela")
    st.dataframe(df)
 
    # Adicionar funcionalidade de download CSV
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="Baixar CSV",
        data=csv_buffer.getvalue(),
        file_name="profile.csv",
        mime="text/csv",
    )