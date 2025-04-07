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
instrumento.timeout= 5000
scanlist = "(@118,116,117,101:105,111,119,112,113,108:110,107,106)"
instrumento.write("CONF:VOLT:DC (@118,116,117,101:105,111,119,112,113,108:110,107,106)")  #Configurar tipo de lectura

#scanlist = "(@101:113,116:119)"
#instrumento.write("CONF:VOLT:DC (@101:116)")  #Configurar tipo de lectura
#setup scan list
instrumento.write("ROUTE:SCAN " + scanlist) #Cosas a escanear
instrumento.write("ROUTE:SCAN:SIZE?") 
numberChannels = int(instrumento.read())+1
print("Número de canales: ", str(numberChannels))
#reading format
instrumento.write("FORMAT:READING:CHAN ON")
instrumento.write("FORMAT:READING:TIME ON")  

numberScans = 5 #Esto lo retocamos ahora
scanIntervals = 5 #5 segundos entre escaneos

#setup when scanning starts and interval rate
instrumento.write("TRIG:COUNT "+str(numberScans))
instrumento.write("TRIG:SOUR TIMER")
instrumento.write("TRIG:TIMER " + str(scanIntervals))
#start the scan and retrieve the scan time
instrumento.write("INIT;:SYSTEM:TIME:SCAN?")   
print (instrumento.read())
points = 0
while (points==0):
    instrumento.write("DATA:POINTS?")
    points=int(instrumento.read())

# Bucle de adquisición de datos
print("Iniciando adquisición de datos... Presiona Ctrl+C para detener.")

try:
    while True:
        # Obtener la hora actual en formato hh:mm:ss
        
        valores = []
        for chan in range(1, numberChannels):
            instrumento.write("DATA:REMOVE? 1")
            read = instrumento.read()
            valores.append(float(read.split(',')[0]))
            points = 0
            #wait for data
            while (points==0):
                instrumento.write("DATA:POINTS?")
                points=int(instrumento.read())

        valores = [round(num) for num in valores]
        valores = [str(num) for num in valores]

        timestamp = datetime.now().strftime("%H:%M:%S")
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
