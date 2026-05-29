import streamlit as st
import pandas as pd
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
import requests
from datetime import datetime
import json
import sqlite3
import os

st.set_page_config(page_title="AquaRuta - Puerto Montt", layout="wide")

DB_FILE = "aquaruta_db.sqlite"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reportes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lat REAL,
            lon REAL,
            nivel TEXT,
            radio INTEGER,
            fecha TEXT,
            geojson TEXT
        )
    ''')
    conn.commit()
    return conn

def obtener_datos():
    conn = init_db()
    df = pd.read_sql_query("SELECT * FROM reportes", conn)
    conn.close()
    return df

def guardar_dato(lat, lon, nivel, radio, fecha, geojson=None):
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reportes (lat, lon, nivel, radio, fecha, geojson)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (lat, lon, nivel, radio, fecha, geojson))
    conn.commit()
    conn.close()

def limpiar_datos():
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM reportes')
    conn.commit()
    conn.close()

@st.cache_data(ttl=300)
def get_weather():
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": -41.4693,
        "longitude": -72.9424,
        "current": "temperature_2m,precipitation,weather_code",
        "hourly": "precipitation_probability,precipitation",
        "daily": "precipitation_sum,precipitation_probability_max",
        "timezone": "America/Santiago",
        "models": "best_match" 
    }
    try:
        res = requests.get(url, params=params, timeout=5)
        if res.status_code == 200:
            return res.json()
    except:
        return None
    return None

def main():
    st.title("💧 AquaRuta")
    
    clima_data = get_weather()
    reportes_df = obtener_datos()
    
    col1, col2 = st.columns([3, 1])
    colores = {"Inundado": "#d32f2f", "Precaución": "#f57c00", "Transitable": "#388e3c"}
    
    with col1:
        m = folium.Map(location=[-41.4693, -72.9424], zoom_start=14, tiles="cartodbpositron")
        
        Draw(
            export=False,
            position="topleft",
            draw_options={
                "polyline": True,
                "polygon": True,
                "circle": True,
                "marker": True,
                "circlemarker": False,
                "rectangle": True,
            }
        ).add_to(m)
        
        if not reportes_df.empty:
            for _, row in reportes_df.iterrows():
                color = colores.get(row["nivel"], "#000000")
                tooltip_text = f"Estado: {row['nivel']} ({row['fecha']})"
                
                if pd.notna(row["geojson"]) and row["geojson"]:
                    try:
                        geo_data = json.loads(row["geojson"])
                        folium.GeoJson(
                            geo_data,
                            style_function=lambda x, color=color: {
                                "fillColor": color,
                                "color": color,
                                "weight": 5,
                                "fillOpacity": 0.6
                            },
                            tooltip=tooltip_text
                        ).add_to(m)
                    except json.JSONDecodeError:
                        pass
                elif pd.notna(row["lat"]) and pd.notna(row["lon"]):
                    folium.Circle(
                        location=[row["lat"], row["lon"]],
                        radius=int(row["radio"]) if pd.notna(row["radio"]) else 150,
                        color=color,
                        fill=True,
                        fill_opacity=0.4,
                        tooltip=tooltip_text
                    ).add_to(m)
        
        mapa = st_folium(m, width=900, height=600, key="mapa")
    
    with col2:
        st.subheader("🌦️ Datos Meteorológicos")
        if clima_data:
            current = clima_data["current"]
            daily = clima_data["daily"]
            hourly = clima_data["hourly"]
            
            c1, c2 = st.columns(2)
            c1.metric("Lluvia Actual", f"{current['precipitation']} mm")
            c2.metric("Lluvia Diaria", f"{daily['precipitation_sum'][0]} mm")
            
            st.metric("Probabilidad Máx. Hoy", f"{daily['precipitation_probability_max'][0]}%")
            
            st.caption("Pronóstico de lluvia (Próximas 12h)")
            hora_actual_idx = int(datetime.now().strftime("%H"))
            df_hourly = pd.DataFrame({
                "Hora": [f"{(hora_actual_idx + i) % 24}:00" for i in range(12)],
                "Precipitación (mm)": hourly["precipitation"][hora_actual_idx:hora_actual_idx+12]
            })
            st.bar_chart(df_hourly.set_index("Hora"))
        else:
            st.warning("No se pudo conectar a la API meteorológica.")

        st.markdown("---")
        st.markdown("### Reportar Calles / Zonas")
        
        lat, lon, geojson_str = None, None, None
        
        if mapa:
            if mapa.get("last_active_drawing"):
                geojson_str = json.dumps(mapa["last_active_drawing"])
                st.info("✅ Zona/ruta registrada.")
            elif mapa.get("last_clicked"):
                lat = mapa["last_clicked"]["lat"]
                lon = mapa["last_clicked"]["lng"]
                st.info(f"📍 Punto: {lat:.4f}, {lon:.4f}")
            else:
                st.info("Selecciona en el mapa...")
        
        with st.form("form_reporte"):
            estado = st.select_slider("Severidad", options=["Transitable", "Precaución", "Inundado"])
            radio = st.slider("Radio (Solo punto único)", 50, 400, 150)
            
            if st.form_submit_button("Guardar Registro"):
                if geojson_str or (lat is not None and lon is not None):
                    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    guardar_dato(lat, lon, estado, radio, fecha_actual, geojson_str)
                    st.rerun()
                else:
                    st.error("Usa el mapa primero.")
            
        if st.button("Limpiar Base de Datos", type="primary", use_container_width=True):
            limpiar_datos()
            st.rerun()

if __name__ == "__main__":
    main()
