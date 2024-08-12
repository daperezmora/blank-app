import streamlit as st
import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import pytz
import time

# Variables para el ID del sensor y el token
token = '9b56e023d84c4c0e9af2d0ee95549392'
id_sensor = 27  # ID del sensor de radiación solar

# Zona horaria del servidor (Ciudad de México sin horario de verano)
timezone = pytz.timezone('America/Mexico_City')

st.title("Dashboard en tiempo real - Radiación Solar")

# Definir una función para obtener el último dato registrado del sensor
def get_last_recorded_data():
    # Configurar el tiempo de inicio como 5 minutos atrás desde el tiempo actual en la zona horaria del servidor
    now = datetime.now(timezone)
    dt_start = (now - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
    dt_end = now.strftime('%Y-%m-%d %H:%M:%S')

    # Construir la URL de la API con los parámetros necesarios
    url = f'http://smability.sidtecmx.com/SmabilityAPI/GetData?token={token}&idSensor={id_sensor}&dtStart={dt_start.replace(" ", "%20")}&dtEnd={dt_end.replace(" ", "%20")}'

    # Realizar la solicitud GET a la API
    response = requests.get(url=url)
    
    # Verificar si la solicitud fue exitosa
    if response.status_code == 200:
        alist = response.json()
        solar_radiation_data = []
        dateTime = []

        for entry in alist:
            solar_radiation = float(entry["Data"])
            solar_radiation_data.append(solar_radiation)
            timestamp = datetime.strptime(entry["TimeStamp"], "%Y-%m-%dT%H:%M:%S")
            timestamp = timezone.localize(timestamp)
            dateTime.append(timestamp)

        return dateTime, solar_radiation_data
    else:
        st.error(f"Error en la extracción de datos: {response.status_code}")
        return [], []

# Mostrar los datos en un gráfico
def display_data():
    dateTime, solar_radiation_data = get_last_recorded_data()

    if dateTime:
        st.subheader("Gráfico de Radiación Solar en Tiempo Real")

        fig, ax = plt.subplots()
        ax.plot(dateTime, solar_radiation_data, 'g-o')
        ax.set_title('Radiación Solar vs. Tiempo')
        ax.set_xlabel('Tiempo')
        ax.set_ylabel('Radiación Solar (W/m^2)')
        ax.grid(True)

        st.pyplot(fig)
    else:
        st.info("Sin datos disponibles para el rango de tiempo especificado.")

# Actualización automática del dashboard cada cierto tiempo
def auto_update(interval=60):
    while True:
        display_data()
        time.sleep(interval)

# Botón para actualizar los datos manualmente
if st.button("Actualizar Datos"):
    display_data()

# Mostrar los datos al cargar la página
display_data()

# Actualización automática (puedes ajustar el intervalo en segundos)
if st.checkbox("Actualizar automáticamente cada 60 segundos"):
    auto_update(60)
