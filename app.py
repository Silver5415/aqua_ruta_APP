import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime

st.set_page_config(page_title="AquaRuta - Puerto Montt", layout="wide")

def main():
    st.title("💧 AquaRuta")
    st.subheader("Estado de inundaciones en tiempo real - Puerto Montt")

    col1, col2 = st.columns([3, 1])

    with col2:
        st.info(f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y')}")
        st.metric(label="Probabilidad de Lluvia", value="85%", delta="Intensa")
        
        st.markdown("### Reportar Incidente")
        sector = st.selectbox("Sector", ["Centro", "Alerce", "Mirasol"])
        nivel = st.select_slider("Nivel de agua", options=["Bajo", "Medio", "Crítico"])
        if st.button("Enviar Reporte"):
            st.success(f"Reporte enviado para {sector}")

    with col1:
        # Coordenadas de Puerto Montt
        m = folium.Map(location=[-41.4693, -72.9424], zoom_start=13, tiles="cartodbpositron")

        # Simulación de estados de calles (Puntos de ejemplo en zonas críticas)
        puntos_criticos = [
            {"loc": [-41.472, -72.942], "estado": "No transitable", "color": "red", "info": "Centro - Inundación alta"},
            {"loc": [-41.400, -72.900], "estado": "Transitable con precaución", "color": "orange", "info": "Alerce - Acumulación de agua"},
            {"loc": [-41.480, -72.960], "estado": "Transitable", "color": "green", "info": "Mirasol - Despejado"}
        ]

        for punto in puntos_criticos:
            folium.CircleMarker(
                location=punto["loc"],
                radius=10,
                color=punto["color"],
                fill=True,
                fill_color=punto["color"],
                popup=punto["info"]
            ).add_to(m)

        # Simulación de Ruta Alternativa (Línea simple)
        ruta_alternativa = [
            [-41.465, -72.930], [-41.468, -72.935], [-41.475, -72.945]
        ]
        folium.PolyLine(ruta_alternativa, color="blue", weight=5, opacity=0.8, tooltip="Ruta Alternativa Segura").add_to(m)

        st_folium(m, width=900, height=500)

    st.markdown("---")
    st.markdown("""
    **Leyenda:**
    - 🔴 **Rojo:** No transitable.
    - 🟠 **Naranja:** Transitable con precaución.
    - 🟢 **Verde:** Transitable.
    - 🔵 **Azul:** Ruta alternativa recomendada.
    """)

if __name__ == "__main__":
    main()
