import pyvisa
import csv
import time
from datetime import datetime

# Configuración de conexión
rm = pyvisa.ResourceManager("@py")
ip_address = "TCPIP::169.254.9.72::INSTR"  # Sustituye con la IP de tu dispositivo
instrumento = rm.open_resource(ip_address)

# Nombre del archivo de salida
txt_filename = "mediciones_keysight.txt"

# Bucle de adquisición de datos
print("Iniciando adquisición de datos... Presiona Ctrl+C para detener.")

try:
    while True:
        # Obtener la hora actual en formato hh:mm:ss
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Solo deja leer 12 canales de una vez
        comando = "MEAS:VOLT? (@101:105)"
        respuesta = instrumento.query(comando)
        # Convertir los datos a una lista de enteros redondeados
        valores = [str(round(float(valor))) for valor in respuesta.split(",")]

        # Crear la línea de salida con tabulaciones
        linea = timestamp + "\t" + "\t".join(valores) + "\n"

        # Guardar en el archivo
        with open(txt_filename, "a") as txtfile:
            txtfile.write(linea)

        print(linea.strip())  # Mostrar en consola

        # Esperar antes de la siguiente medición
        time.sleep(2)  # Ajusta el tiempo según necesidad

except KeyboardInterrupt:
    print("\nAdquisición detenida por el usuario.")

# Cerrar conexión
instrumento.close()