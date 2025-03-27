import pyvisa
import time
from datetime import datetime

# Configuración de conexión
rm = pyvisa.ResourceManager("@py")
ip_address = "TCPIP::169.254.9.72::INSTR"  # Sustituye con la IP de tu dispositivo
instrumento = rm.open_resource(ip_address)

# Nombre del archivo de salida
txt_filename = "mediciones_keysight.txt"

# Configuración de muestreo del equipo (si es aplicable)
# Aquí asumimos que el equipo tiene un comando para configurar el intervalo de muestreo
# Si tu equipo lo soporta, podrías usar algo como:
scanlist = "(@101:116)"
instrumento.write("*CLS")     #clear 
instrumento.write("*RST")     #reset 
instrumento.write("CONF:VOLT:DC (@101:116)")  
instrumento.write("TRIG:TIMER " + str(5))
instrumento.timeout= 5000

# Bucle de adquisición de datos
print("Iniciando adquisición de datos... Presiona Ctrl+C para detener.")

try:
    while True:
        # Obtener la hora actual en formato hh:mm:ss
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Leer cada canal individualmente (canales 101 a 105)
        valores = []
        
        comando = f"MEAS:VOLT? (@101:116)"
        respuesta = instrumento.query(comando)
        # Convertir el dato a un número redondeado
        valores = [float(num) for num in respuesta.strip().split(',')]
        valores = [round(num) for num in valores]
        valores = [str(num) for num in valores]

        # Crear la línea de salida con tabulaciones
        linea = timestamp + "\t" + "\t".join(valores) + "\n"

        # Guardar en el archivo
        with open(txt_filename, "a") as txtfile:
            txtfile.write(linea)

        print(linea.strip())  # Mostrar en consola

        # Esperar antes de la siguiente medición


except KeyboardInterrupt:
    print("\nAdquisición detenida por el usuario.")

# Cerrar conexión
instrumento.close()
