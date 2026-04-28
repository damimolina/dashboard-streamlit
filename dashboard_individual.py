


import streamlit as st
import pandas as pd
import folium
import json
from folium.plugins import HeatMap
from streamlit_folium import st_folium


#--------------------------- CONFIGURACIÓN-------------------

st.set_page_config(layout="wide")
st.title("Dashboard de Ventas Geoespacial")
st.write("Autor: Alberto Molina")
st.write("Análisis interactivo de ventas, distribución y comportamiento del cliente")


# ---------------------------CARGA Y LIMPIEZA-----------------

@st.cache_data
def load_data():
    df = pd.read_excel('dataset_tarea_ind.xlsx')

    cols_numericas = ['venta_neta', 'lat', 'lng', 'kms_dist', 'lat_cd', 'lng_cd']

    for col in cols_numericas:
        df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df['fecha_compra'] = pd.to_datetime(df['fecha_compra'], format='%d-%m-%y', errors='coerce')

    df = df.dropna()

    df['canal'] = df['canal'].str.lower()
    df['state'] = df['state'].str.upper()

    return df

df = load_data()


#--------------------------- FILTROS

st.sidebar.header("Filtros")

canal = st.sidebar.multiselect(
    "Canal",
    df["canal"].unique(),
    default=df["canal"].unique()
)

ventas_min = st.sidebar.slider(
    "Venta mínima",
    int(df["venta_neta"].min()),
    int(df["venta_neta"].max()),
    int(df["venta_neta"].min())
)

df = df[
    (df["canal"].isin(canal)) &
    (df["venta_neta"] >= ventas_min)
]


# ----------------------------ANÁLISIS 1 - GRÁFICOS

st.subheader("Ventas por canal")
st.bar_chart(df.groupby('canal')['venta_neta'].sum())

st.subheader("Ventas por centro de distribución")
st.bar_chart(df.groupby('centro_dist')['venta_neta'].sum())

st.subheader("Evolución de ventas en el tiempo")
st.line_chart(df.groupby('fecha_compra')['venta_neta'].sum())


#------------------------------ MAPA PRINCIPAL

st.subheader("Mapa de clientes y centros de distribución")

mapa = folium.Map(
    location=[df['lat'].mean(), df['lng'].mean()],
    zoom_start=10,
    tiles='cartodbpositron'
)

cds = df[['centro_dist', 'lat_cd', 'lng_cd']].drop_duplicates()

for _, row in cds.iterrows():
    folium.Marker(
        [row['lat_cd'], row['lng_cd']],
        popup=f"CD: {row['centro_dist']}",
        icon=folium.Icon(color='red')
    ).add_to(mapa)

sample = df.sample(min(800, len(df)))

for _, row in sample.iterrows():
    folium.CircleMarker(
        [row['lat'], row['lng']],
        radius=3,
        color='blue',
        fill=True,
        fill_opacity=0.6,
        popup=f"Venta: {row['venta_neta']}"
    ).add_to(mapa)

st_folium(mapa, width=900, height=500)


#--------------------------------- HEATMAP

st.subheader("Heatmap de densidad de clientes")

mapa_heat = folium.Map(
    location=[df['lat'].mean(), df['lng'].mean()],
    zoom_start=10,
    tiles='cartodbpositron'
)

heat_data = df[['lat', 'lng']].values.tolist()
HeatMap(heat_data, radius=10, blur=15).add_to(mapa_heat)

st_folium(mapa_heat, width=900, height=500)


#--------------------------------- COROPLETA

st.subheader("Ventas por comuna (Coropleta)")

with open('comunas_metropolitana-1.geojson', encoding='utf-8') as f:
    geojson_data = json.load(f)

ventas_comuna = df.groupby('comuna')['venta_neta'].sum().reset_index()

mapa_coropleta = folium.Map(
    location=[df['lat'].mean(), df['lng'].mean()],
    zoom_start=10,
    tiles='cartodbpositron'
)

folium.Choropleth(
    geo_data=geojson_data,
    data=ventas_comuna,
    columns=['comuna', 'venta_neta'],
    key_on='feature.properties.name',
    fill_color='YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Ventas por comuna'
).add_to(mapa_coropleta)

st_folium(mapa_coropleta, width=900, height=500)


# ------------------------------------ANÁLISIS 5 

st.subheader("Comunas por ticket promedio")

df["ticket_promedio"] = df["venta_neta"] / df["orden"]

ticket_comuna = (
    df.groupby("comuna")["ticket_promedio"]
    .mean()
    .sort_values(ascending=False)
    .head(10)
)

st.dataframe(ticket_comuna)
st.bar_chart(ticket_comuna)

#
#------------------------------ DESCRIPCION DEL DASHBOARD

st.write("""
Este dashboard permite analizar ventas desde múltiples perspectivas:
- Canales de venta
- Centros de distribución
- Ubicación geográfica
- Densidad de clientes
- Ticket promedio por comuna

Los filtros permiten explorar diferentes escenarios de negocio de forma interactiva.
""")