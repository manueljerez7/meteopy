import pyvisa
import time
from datetime import datetime

# Fichero para resetear el equipo
rm = pyvisa.ResourceManager("@py")
ip_address = "TCPIP::169.254.9.72::INSTR"  
instrumento = rm.open_resource(ip_address)
instrumento.write("*CLS")     #clear 
instrumento.write("*RST")     #reset 