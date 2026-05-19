import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
from datetime import datetime

st.set_page_config(page_title="AquaRuta - Puerto Montt", layout="wide")

@st.cache_data(ttl=300)
def get_cr2_meteo():
    url = "https://api.open-meteo.com/v1/forecast?latitude=-41.4693&longitude=-72.9424&current=precipitation,rain&timezone=America/Santiago"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "lluvia_mm": data.get("current", {}).get("precipitation", 0.0),
                "fuente": "Open-Meteo (Estación Puerto Montt)"
            }
    except:
        pass
    return {"lluvia_mm": 0.0, "fuente": "Simulado (Error de conexión)"}

if "reportes" not in st.session_state:
    st.session_state.reportes = pd.DataFrame(columns=["Sector", "Lat", "Lon", "Nivel", "Radio", "Fecha"])

def main():
    st.title("💧 AquaRuta")
    st.subheader("Plataforma en tiempo real por zonas de afectación")

    datos_clima = get_cr2_meteo()
    lluvia_actual = datos_clima["lluvia_mm"]

    col1, col2 = st.columns([3, 1])

    with col2:
        st.metric(
            label=f"Precipitación Actual ({datos_clima['fuente']})", 
            value=f"{lluvia_actual} mm", 
            delta="Riesgo de anegamiento" if lluvia_actual > 1.0 else "Normal"
        )
        
        st.markdown("---")
        st.subheader("📍 Reportar Área Inundada")
        
        with st.form("zona_form", clear_on_submit=True):
            zona_predefinida = st.selectbox("Sector Crítico", ["Centro", "Alerce", "Mirasol", "Otro (Hacer clic en mapa)"])
            
            st.caption("Si seleccionas 'Otro', se usarán las coordenadas por defecto o las del último clic.")
            
            estado = st.select_slider("Severidad del agua", options=["Transitable", "Precaución", "Inundado"])
            radio = st.slider("Radio estimado del área (metros)", 50, 500, 150)
            
            submitted = st.form_submit_button("Dibujar Zona en Mapa")
            
            if submitted:
                coordenadas = {
                    "Centro": [-41.4718, -72.9419],
                    "Alerce": [-41.4022, -72.9031],
                    "Mirasol": [-41.4782, -72.9645],
                    "Otro (Hacer clic en mapa)": [-41.4693, -72.9424]
                }
                
                pos = coordenadas[zona_predefinida]
                
                nuevo_reporte = pd.DataFrame([{
                    "Sector": zona_predefinida,
                    "Lat": pos[0],
                    "Lon": pos[1],
                    "Nivel": estado,
                    "Radio": radio,
                    "Fecha": datetime.now().strftime("%H:%M:%S")
                }])
                
                st.session_state.reportes = pd.concat([st.session_state.reportes, nuevo_reporte], ignore_index=True)
                st.success(f"Área de acumulación registrada para {zona_predefinida}.")
                st.rerun()

        if st.button("Limpiar Mapa"):
            st.session_state.reportes = pd.DataFrame(columns=["Sector", "Lat", "Lon", "Nivel", "Radio", "Fecha"])
            st.rerun()

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
                fill_opacity=0.45,
                popup=f"<b>Sector:</b> {row['Sector']}<br><b>Estado:</b> {row['Nivel']}<br><b>Reportado a las:</b> {row['Fecha']}"
            ).add_to(m)

        if lluvia_actual > 2.0:
            folium.Circle(
                location=[-41.4718, -72.9419],
                radius=600,
                color="#b71c1c",
                fill=True,
                fill_color="#b71c1c",
                fill_opacity=0.2,
                popup="<b>Alerta Automática:</b> Alta probabilidad de acumulación por lluvias intensas en el Centro."
            ).add_to(m)

        st_folium(m, width=900, height=600, key="mapa_aquaruta")

if __name__ == "__main__":
    main()
