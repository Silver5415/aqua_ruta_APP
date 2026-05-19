import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

st.set_page_config(page_title="AquaRuta - Puerto Montt", layout="wide")

# --- BASE DE DATOS (Google Sheets & Local CSV Fallback) ---
def init_db():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        if "gcp_service_account" in st.secrets:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
            client = gspread.authorize(creds)
            sheet = client.open("AquaRuta_DB").sheet1
            return sheet
    except Exception:
        pass
    return None

sheet = init_db()
DB_LOCAL = "aquaruta_db.csv"

def obtener_datos():
    if sheet:
        try:
            records = sheet.get_all_records()
            if records:
                return pd.DataFrame(records)
        except:
            pass
    if os.path.exists(DB_LOCAL):
        return pd.read_csv(DB_LOCAL)
    return pd.DataFrame(columns=["Lat", "Lon", "Nivel", "Radio", "Fecha"])

def guardar_dato(lat, lon, nivel, radio, fecha):
    nuevo = {"Lat": lat, "Lon": lon, "Nivel": nivel, "Radio": radio, "Fecha": fecha}
    if sheet:
        try:
            if len(sheet.get_all_values()) == 0:
                sheet.append_row(["Lat", "Lon", "Nivel", "Radio", "Fecha"])
            sheet.append_row([lat, lon, nivel, radio, fecha])
        except:
            pass
    
    df = obtener_datos()
    df = pd.concat([df, pd.DataFrame([nuevo])], ignore_index=True)
    df.to_csv(DB_LOCAL, index=False)

def limpiar_datos():
    if sheet:
        try:
            sheet.clear()
            sheet.append_row(["Lat", "Lon", "Nivel", "Radio", "Fecha"])
        except:
            pass
    if os.path.exists(DB_LOCAL):
        os.remove(DB_LOCAL)

# --- APIS ---
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
    headers = {'User-Agent': 'AquaRuta-Prototipo/1.0'}
    try:
        res = requests.get(overpass_url, params={'data': query}, headers=headers, timeout=10)
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return None

# --- APP ---
def main():
    st.title("💧 AquaRuta")
    
    lluvia = get_weather()
    reportes_df = obtener_datos()
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        m = folium.Map(location=[-41.4693, -72.9424], zoom_start=14, tiles="cartodbpositron")
        colores = {"Inundado": "#d32f2f", "Precaución": "#f57c00", "Transitable": "#388e3c"}
        
        if not reportes_df.empty:
            for _, row in reportes_df.iterrows():
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
        
        if sheet is None:
            st.warning("Google Sheets no conectado (Faltan secrets). Usando CSV local para que funcione.")
        else:
            st.success("Google Sheets conectado.")

        st.markdown("### Reportar Calles")
        
        lat, lon = -41.4693, -72.9424
        if mapa and mapa.get("last_clicked"):
            lat = mapa["last_clicked"]["lat"]
            lon = mapa["last_clicked"]["lng"]
            st.info(f"Coordenadas: {lat:.4f}, {lon:.4f}")
        else:
            st.info("Haz clic en el mapa para marcar el centro de la zona.")
        
        with st.form("form_reporte"):
            estado = st.select_slider("Severidad", options=["Transitable", "Precaución", "Inundado"])
            radio = st.slider("Radio de búsqueda (metros)", 50, 400, 150)
            
            if st.form_submit_button("Marcar Calles"):
                if mapa and mapa.get("last_clicked"):
                    fecha_actual = datetime.now().strftime("%H:%M:%S")
                    guardar_dato(lat, lon, estado, radio, fecha_actual)
                    st.rerun()
                else:
                    st.error("Por favor, haz clic en el mapa primero.")
                
        if st.button("Limpiar Base de Datos"):
            limpiar_datos()
            st.rerun()

if __name__ == "__main__":
    main()
