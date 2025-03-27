import pyvisa

# Crear el recurso de VISA
rm = pyvisa.ResourceManager("@py")

instrumento = rm.open_resource("TCPIP::169.254.9.72::INSTR")

instrumento.write("*IDN?")  # Algunos dispositivos responden a este comando

# Leer la respuesta
respuesta = instrumento.read()
print(f"Respuesta del dispositivo: {respuesta}")

instrumento.timeout = 2000
instrumento.write("*CLS")     #clear 
instrumento.write("*RST")     #reset 


'''Set Variables'''
scanIntervals = 5      #Delay in secs, between scans
numberScans = 5         #Number of scan sweeps to measure
channelDelay = 0.01      #Delay, in secs, between relay closure and measurement 
points = 0              #number of data points stored
voltage = 2.00          #voltage value to DAC from -12 to 12

'''
scanlist does not have to include all configured channels
In this example 103 is excluded to illustrate
'''
scanlist = "(@101:116)"

instrumento.write("CONF:VOLT:DC (@101:116)")  
#setup scan list
instrumento.write("ROUTE:SCAN " + scanlist) 
instrumento.write("ROUTE:SCAN:SIZE?") 
numberChannels = int(instrumento.read())+1
#reading format
instrumento.write("FORMAT:READING:CHAN ON")
instrumento.write("FORMAT:READING:TIME ON")  
#channel delay
#instrumento.write("ROUT:CHAN:DELAY " + str(channelDelay)+","+scanlist)
#setup when scanning starts and interval rate
instrumento.write("TRIG:COUNT "+str(numberScans))
instrumento.write("TRIG:SOUR TIMER")
instrumento.write("TRIG:TIMER " + str(scanIntervals))
#start the scan and retrieve the scan time
instrumento.write("INIT;:SYSTEM:TIME:SCAN?")   
print (instrumento.read())
'''wait until there is a data available'''
points = 0
while (points==0):
    instrumento.write("DATA:POINTS?")
    points=int(instrumento.read())

'''
The data points are printed 
data, time, channel
'''
x = 0
while x < numberScans:
    
    valores = []
    for chan in range(1, numberChannels):
        instrumento.write("DATA:REMOVE? 1")
        read = instrumento.read()
        print (read)
        valores.append(float(read.split(',')[0]))
        points = 0
        #wait for data
        while (points==0):
            instrumento.write("DATA:POINTS?")
            points=int(instrumento.read())

    valores = [round(num) for num in valores]
    valores = [str(num) for num in valores]
    linea = "CAD" + "\t" + "\t".join(valores) + "\n"
    print(linea.strip())  # Mostrar en consola
    x += 1
    
    

#Close   
instrumento.close()
print('close instrument connection')