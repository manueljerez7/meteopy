import pyvisa
import time
from datetime import datetime

# Configuración de conexión
rm = pyvisa.ResourceManager("@py")
ip_address = "TCPIP::169.254.9.72::INSTR"  # Sustituye con la IP de tu dispositivo
instrumento = rm.open_resource(ip_address)

numero_dia = datetime.today().strftime('%j')
# Generar el nombre del archivo
txt_filename = f"meteo_{numero_dia}.txt"

# Configuración de muestreo del equipo
# Aquí asumimos que el equipo tiene un comando para configurar el intervalo de muestreo
# Si tu equipo lo soporta, podrías usar algo como:
instrumento.write("*CLS")     #clear 
instrumento.write("*RST")     #reset 