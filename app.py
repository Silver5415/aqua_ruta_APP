import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
from datetime import datetime

st.set_page_config(page_title="AquaRuta - Puerto Montt", layout="wide")

@st.cache_data(ttl=300)
def get_weather():
    url = "https://api.open-meteo.com/v1/forecast?latitude=-41.4693&longitude=-72.9424&current=precipitation&timezone=America/Santiago"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.json().get("current", {}).get("precipitation", 0.0)
    except:
        return 0.0
    return 0.0

@st.cache_data(ttl=600)
def get_calles_overpass(lat, lon, radio):
    overpass_url = "http://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    way(around:{radio},{lat},{lon})["highway"~"primary|secondary|tertiary|residential|unclassified"];
    out geom;
    """
    headers = {'User-Agent': 'AquaRuta-Prototipo-USS/1.0'}
    try:
        res = requests.get(overpass_url, params={'data': query}, headers=headers, timeout=10)
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return None

if "reportes" not in st.session_state:
    st.session_state.reportes = pd.DataFrame(columns=["Lat", "Lon", "Nivel", "Radio", "Fecha"])

def main():
    st.title("💧 AquaRuta")
    
    lluvia = get_weather()
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        m = folium.Map(location=[-41.4693, -72.9424], zoom_start=14, tiles="cartodbpositron")
        colores = {"Inundado": "#d32f2f", "Precaución": "#f57c00", "Transitable": "#388e3c"}
        
        if not st.session_state.reportes.empty:
            for _, row in st.session_state.reportes.iterrows():
                datos_calles = get_calles_overpass(row["Lat"], row["Lon"], row["Radio"])
                
                calles_dibujadas = False
                if datos_calles and 'elements' in datos_calles:
                    for element in datos_calles['elements']:
                        if 'geometry' in element:
                            puntos = [(pt['lat'], pt['lon']) for pt in element['geometry']]
                            if puntos:
                                folium.PolyLine(
                                    puntos, 
                                    color=colores[row["Nivel"]], 
                                    weight=6, 
                                    opacity=0.9,
                                    tooltip=f"Estado: {row['Nivel']} ({row['Fecha']})"
                                ).add_to(m)
                                calles_dibujadas = True
                
                if not calles_dibujadas:
                    folium.Circle(
                        location=[row["Lat"], row["Lon"]],
                        radius=int(row["Radio"]),
                        color=colores[row["Nivel"]],
                        fill=True,
                        fill_opacity=0.4,
                        tooltip=f"Estado: {row['Nivel']} ({row['Fecha']})"
                    ).add_to(m)
            
        mapa = st_folium(m, width=900, height=600, key="mapa")
    
    with col2:
        st.metric(label="Precipitación Actual (Open-Meteo)", value=f"{lluvia} mm")
        st.markdown("### Reportar Calles")
        
        lat, lon = -41.4693, -72.9424
        if mapa and mapa.get("last_clicked"):
            lat = mapa["last_clicked"]["lat"]
            lon = mapa["last_clicked"]["lng"]
            st.success(f"Coordenadas: {lat:.4f}, {lon:.4f}")
        else:
            st.info("Haz clic en el mapa para marcar el centro de la zona.")
        
        with st.form("form_reporte"):
            estado = st.select_slider("Severidad", options=["Transitable", "Precaución", "Inundado"])
            radio = st.slider("Radio de búsqueda (metros)", 50, 400, 150)
            
            if st.form_submit_button("Marcar Calles"):
                if mapa and mapa.get("last_clicked"):
                    nuevo = pd.DataFrame([{
                        "Lat": lat,
                        "Lon": lon,
                        "Nivel": estado,
                        "Radio": radio,
                        "Fecha": datetime.now().strftime("%H:%M:%S")
                    }])
                    if not nuevo.empty:
                        st.session_state.reportes = pd.concat([st.session_state.reportes, nuevo], ignore_index=True)
                        st.rerun()
                else:
                    st.error("Por favor, haz clic en el mapa primero.")
                
        if st.button("Limpiar Mapa"):
            st.session_state.reportes = pd.DataFrame(columns=["Lat", "Lon", "Nivel", "Radio", "Fecha"])
            st.rerun()

if __name__ == "__main__":
    main()
