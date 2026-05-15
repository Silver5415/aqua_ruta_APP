import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
from datetime import datetime

# Configuración de página
st.set_page_config(page_title="AquaRuta - Puerto Montt", layout="wide")

# Función para obtener datos reales de clima
def get_weather_data(api_key):
    city = "Puerto Montt"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=es"
    try:
        response = requests.get(url)
        return response.json()
    except:
        return None

def main():
    st.title("💧 AquaRuta")
    st.write("Visualización colaborativa con datos meteorológicos reales.")

    # Simulación de API KEY (En producción usar st.secrets)
    # Puedes obtener una gratis en openweathermap.org
    API_KEY = "tu_api_key_aqui" 
    weather = get_weather_data(API_KEY)

    col1, col2 = st.columns([3, 1])

    with col2:
        if weather and weather.get("main"):
            temp = weather["main"]["temp"]
            desc = weather["weather"][0]["description"]
            # Extraer lluvia en la última hora si existe
            rain_1h = weather.get("rain", {}).get("1h", 0)
            
            st.metric("Lluvia (última hora)", f"{rain_1h} mm", delta="Intensa" if rain_1h > 2 else "Moderada")
            st.write(f"🌡️ Temp: {temp}°C | ☁️ {desc.capitalize()}")
            
            # Lógica de riesgo automática según mm de lluvia
            riesgo_auto = "Bajo"
            if rain_1h > 5: riesgo_auto = "Crítico"
            elif rain_1h > 1: riesgo_auto = "Medio"
        else:
            st.warning("No se pudo conectar con la API de clima. Usando datos simulados.")
            rain_1h = 0.5
            riesgo_auto = "Medio"

        st.markdown("---")
        st.subheader("📢 Reporte Ciudadano")
        with st.form("report_form"):
            sector = st.selectbox("Sector", ["Centro", "Alerce", "Mirasol"])
            nivel = st.select_slider("Estado observado", options=["Transitable", "Precaución", "Inundado"])
            # Se corrigió a st.form_submit_button
            submitted = st.form_submit_button("Enviar Reporte")
            if submitted:
                st.success(f"Gracias, reporte para {sector} recibido.")

    with col1:
        # Mapa base
        m = folium.Map(location=[-41.4693, -72.9424], zoom_start=13, tiles="cartodbpositron")

        # Puntos de interés basados en la lluvia real + diseño F11
        puntos = [
            {"loc": [-41.472, -72.942], "nombre": "Centro", "base_color": "red" if rain_1h > 3 else "orange"},
            {"loc": [-41.400, -72.900], "nombre": "Alerce", "base_color": "red" if rain_1h > 5 else "green"},
            {"loc": [-41.480, -72.960], "nombre": "Mirasol", "base_color": "orange" if rain_1h > 2 else "green"}
        ]

        for p in puntos:
            folium.Marker(
                location=p["loc"],
                popup=f"{p['nombre']} - Riesgo: {p['base_color']}",
                icon=folium.Icon(color=p["base_color"], icon="info-sign")
            ).add_to(m)

        # Dibujar Ruta Alternativa (F9: 3 zonas críticas)
        ruta = [[-41.465, -72.930], [-41.468, -72.935], [-41.475, -72.945]]
        folium.PolyLine(ruta, color="blue", weight=4, tooltip="Ruta Segura Sugerida").add_to(m)

        st_folium(m, width=800, height=500)

if __name__ == "__main__":
    main()
