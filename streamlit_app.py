import streamlit as st
import requests
import pyvisa
from datetime import datetime, timedelta
import pytz
import matplotlib.pyplot as plt

# Variables para el ID del sensor y el token
token = '9b56e023d84c4c0e9af2d0ee95549392'
id_sensor = 27  # ID del sensor de radiación solar

# Zona horaria del servidor (Ciudad de México sin horario de verano)
timezone = pytz.timezone('America/Mexico_City')

# Características del panel solar
area = 1.0  # m^2
efficiency = 0.20  # 20%
Vmpp = 90  # Voltaje en el punto de máxima potencia
Impp = 2.45  # Corriente en el punto de máxima potencia
Pmpp = Vmpp * Impp  # Potencia en el punto de máxima potencia

st.title("Simulación de tiempo real de un panel solar")

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
        power_data = []
        voltage_data = []
        current_data = []

        for entry in alist:
            solar_radiation = float(entry["Data"])
            solar_radiation_data.append(solar_radiation)
            timestamp = datetime.strptime(entry["TimeStamp"], "%Y-%m-%dT%H:%M:%S")
            timestamp = timezone.localize(timestamp)
            dateTime.append(timestamp)

            P_gen = round(solar_radiation * area * efficiency, 2)
            power_data.append(P_gen)

            if P_gen > 0:
                V = round(Vmpp * (P_gen / Pmpp) ** 0.5, 2)
                I = round(Impp * (P_gen / Pmpp) ** 0.5, 2)
                if V > Vmpp:
                    V = Vmpp
                if I > Impp:
                    I = Impp
            else:
                V = 0
                I = 0

            voltage_data.append(V)
            current_data.append(I)

        return dateTime, solar_radiation_data, power_data, voltage_data, current_data

    else:
        st.error(f"Error en la extracción de datos: {response.status_code}")
        return [], [], [], [], []

# Definir una función para mostrar los datos
def display_data():
    dateTime, solar_radiation_data, power_data, voltage_data, current_data = get_last_recorded_data()
    
    if dateTime:
        st.subheader("Datos en tiempo real")
        
        for dt, radiation, power, V, I in reversed(list(zip(dateTime, solar_radiation_data, power_data, voltage_data, current_data))):
            st.write(f"Tiempo: {dt.strftime('%Y-%m-%d %H:%M:%S')}, Radiación Solar: {radiation} W/m^2, Potencia: {power} W, Voltaje: {V} V, Corriente: {I} A")
        
        fig, ax = plt.subplots(3, 1, figsize=(10, 12))

        ax[0].plot(dateTime, power_data, 'g-o')
        ax[0].set_title('Potencia vs. Tiempo')
        ax[0].set_ylabel('Potencia (W)')
        ax[0].grid(True)

        ax[1].plot(dateTime, voltage_data, 'b-o')
        ax[1].set_title('Voltaje vs. Tiempo')
        ax[1].set_ylabel('Voltaje (V)')
        ax[1].grid(True)

        ax[2].plot(dateTime, current_data, 'r-o')
        ax[2].set_title('Corriente vs. Tiempo')
        ax[2].set_ylabel('Corriente (A)')
        ax[2].grid(True)

        plt.tight_layout()
        st.pyplot(fig)

        # Control del dispositivo usando pyvisa
        try:
            rm = pyvisa.ResourceManager()
            instrument = rm.open_resource('USB0::0xXXXX::0xYYYY::INSTR')
            instrument.write('*RST')
            instrument.write(f'VOLT {voltage_data[-1]}\n')
            instrument.write(f'CURR {current_data[-1]}\n')
            instrument.write('OUTP ON\n')
            instrument.close()
        except Exception as e:
            st.warning("No se pudo conectar con el dispositivo: " + str(e))
    else:
        st.info("Sin datos disponibles para el rango de tiempo especificado.")

# Agregar un botón para iniciar la simulación
if st.button("Iniciar Simulación"):
    display_data()

st.write("Presiona el botón para obtener datos en tiempo real.")
