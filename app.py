import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
import gspread # Necesitarás configurar las credenciales de Google
from oauth2client.service_account import ServiceAccountCredentials

# 1. Configuración de la base de datos (Google Sheets)
def get_data_from_gsheets():
    # Solo como ejemplo de estructura, aquí leerías tu Google Sheet
    # En un prototipo real, usarías gspread para traer los reportes
    # Por ahora simulamos la "Base de datos" que se alimentaría de los reportes
    data = {
        'Sector': ['Centro', 'Alerce', 'Mirasol'],
        'Lat': [-41.472, -41.400, -41.480],
        'Lon': [-72.942, -72.900, -72.960],
        'Nivel': ['Inundado', 'Precaución', 'Transitable'],
        'Radio': [300, 500, 400] # Metros de la esfera/zona
    }
    return pd.DataFrame(data)

def main():
    st.set_page_config(page_title="AquaRuta Real-Time", layout="wide")
    st.title("💧 AquaRuta: Monitoreo por Zonas")

    # Colores según nivel para las esferas
    colores = {"Inundado": "red", "Precaución": "orange", "Transitable": "green"}

    col1, col2 = st.columns([3, 1])

    with col2:
        st.subheader("📍 Nuevo Reporte de Zona")
        with st.form("report_form"):
            sector = st.selectbox("Seleccionar Sector", ["Centro", "Alerce", "Mirasol"])
            estado = st.select_slider("Estado de la zona", options=["Transitable", "Precaución", "Inundado"])
            # El usuario define qué tan grande es la afectación (la esfera)
            radio_zona = st.slider("Radio de afectación (metros)", 100, 1000, 300)
            
            submitted = st.form_submit_button("Publicar en Mapa")
            if submitted:
                # Aquí iría el código: sheet.append_row([sector, estado, radio_zona, datetime.now()])
                st.success(f"Zona {sector} actualizada en la base de datos.")
                st.rerun() # Refresca la app para mostrar el nuevo dato

    with col1:
        df_reportes = get_data_from_gsheets()
        
        # Mapa centrado en Puerto Montt
        m = folium.Map(location=[-41.4693, -72.9424], zoom_start=12, tiles="cartodbpositron")

        # Generar las esferas de riesgo en lugar de líneas de calle
        for _, row in df_reportes.iterrows():
            folium.Circle(
                location=[row['Lat'], row['Lon']],
                radius=row['Radio'],
                color=colores[row['Nivel']],
                fill=True,
                fill_opacity=0.4,
                popup=f"Sector: {row['Sector']}\nEstado: {row['Nivel']}"
            ).add_to(m)

        st_folium(m, width=900, height=600)

if __name__ == "__main__":
    main()
