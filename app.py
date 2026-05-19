import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
from datetime import datetime

st.set_page_config(page_title="AquaRuta - Puerto Montt", layout="wide")

@st.cache_data(ttl=300)
def get_weather():
    url = "https://api.open-meteo.com/v1/forecast?latitude=-41.4693&longitude=-72.9424&current=precipitation&hourly=precipitation,precipitation_probability&timezone=America/Santiago&forecast_days=2"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            current_rain = data.get("current", {}).get("precipitation", 0.0)
            
            times = data.get("hourly", {}).get("time", [])
            rains = data.get("hourly", {}).get("precipitation", [])
            probs = data.get("hourly", {}).get("precipitation_probability", [])
            
            forecast = []
            now_str = datetime.now().strftime("%Y-%m-%dT%H:00")
            
            try:
                idx = 0
                for i, t in enumerate(times):
                    if t >= now_str:
                        idx = i
                        break
                        
                for i in range(1, 5):
                    if idx + i < len(times):
                        hora_format = times[idx+i].split("T")[1]
                        forecast.append({
                            "hora": hora_format,
                            "lluvia": rains[idx+i],
                            "probabilidad": probs[idx+i]
                        })
            except Exception:
                pass
                
            return current_rain, forecast
    except:
        return 0.0, []
    return 0.0, []

if "reportes" not in st.session_state:
    st.session_state.reportes = pd.DataFrame(columns=["Lat", "Lon", "Nivel", "Radio", "Fecha"])

def main():
    st.title("💧 AquaRuta")
    
    lluvia, pronostico = get_weather()
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        m = folium.Map(location=[-41.4693, -72.9424], zoom_start=13, tiles="cartodbpositron")
        
        colores = {"Inundado": "#d32f2f", "Precaución": "#f57c00", "Transitable": "#388e3c"}
        
        for _, row in st.session_state.reportes.iterrows():
            folium.Circle(
                location=[row["Lat"], row["Lon"]],
                radius=int(row["Radio"]),
                color=colores[row["Nivel"]],
                fill=True,
                fill_color=colores[row["Nivel"]],
                fill_opacity=0.5,
                popup=f"Estado: {row['Nivel']}<br>Hora: {row['Fecha']}"
            ).add_to(m)
            
        mapa = st_folium(m, width=900, height=600, key="mapa")
    
    with col2:
        st.metric(label="Precipitación Actual (Open-Meteo)", value=f"{lluvia} mm")
        
        if pronostico:
            st.markdown("### Pronóstico (próximas horas)")
            for p in pronostico:
                st.write(f"**{p['hora']}**: {p['lluvia']} mm ({p['probabilidad']}% prob.)")
        
        st.markdown("---")
        st.markdown("### Reportar Acumulación")
        
        lat, lon = -41.4693, -72.9424
        if mapa and mapa.get("last_clicked"):
            lat = mapa["last_clicked"]["lat"]
            lon = mapa["last_clicked"]["lng"]
            st.success("Coordenadas capturadas.")
        else:
            st.info("Haz clic en un punto del mapa para seleccionar la ubicación exacta.")
        
        with st.form("form_reporte"):
            estado = st.select_slider("Severidad", options=["Transitable", "Precaución", "Inundado"])
            radio = st.slider("Radio de acumulación (metros)", 50, 500, 150)
            
            if st.form_submit_button("Agregar Zona"):
                if mapa and mapa.get("last_clicked"):
                    nuevo = pd.DataFrame([{
                        "Lat": lat,
                        "Lon": lon,
                        "Nivel": estado,
                        "Radio": radio,
                        "Fecha": datetime.now().strftime("%H:%M:%S")
                    }])
                    st.session_state.reportes = pd.concat([st.session_state.reportes, nuevo], ignore_index=True)
                    st.rerun()
                else:
                    st.error("Debes hacer clic en el mapa primero.")
                
        if st.button("Limpiar Mapa"):
            st.session_state.reportes = pd.DataFrame(columns=["Lat", "Lon", "Nivel", "Radio", "Fecha"])
            st.rerun()

if __name__ == "__main__":
    main()
