
import pyvisa  # for scpi
import time  # for sleep
import logging
import time
from datetime import datetime
import os
# INT_ID = "USB0::4883::32802::M00450923::0::INSTR"

DELAY = 0.1
numero_dia = datetime.today().strftime('%j')
año = datetime.today().strftime('%Y')
DATA_FILE = f"meteo_{año}_{numero_dia}.txt"
CONFIG_FILE = "config.txt"
DEVICES_FILE = "devices.txt"


def load_multiplicadores():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            valores = f.readlines()
        return [float(v.strip()) for v in valores]
    else:
        return [1.0] * 17

def open_session():
    logging.basicConfig(
        filename="logfile.log",
        filemode="a",
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%d-%b-%y %H:%M:%S",
        level=logging.INFO,
        #level=logging.DEBUG,
    )

    try:
        visa_handler = pyvisa.ResourceManager("@py")
        # rm = pyvisa.ResourceManager()
        logging.info("Openning measurements session")
        logging.info("VISA session open")

        address = "TCPIP::169.254.9.72::INSTR"

                
        logging.info("Openning device with address:"+address)

        inst_handler = visa_handler.open_resource(address)
        time.sleep(DELAY)

        inst_handler.query_delay = DELAY
        time.sleep(DELAY)
            
        
        time.sleep(DELAY)
        logging.info("Session and meter open")

        return visa_handler, inst_handler
    
            
    except Exception as e:
        print(e)
        logging.error("Exception occurred during session openning", exc_info=True)

        exit()

def close_session(visa_handler, inst_handler):
    try:
        inst_handler.write("*RST")     #reset 
        
        logging.info("Closing session")
        inst_handler.close()
        visa_handler.close()
        
        logging.info("Session closed")
        logging.getLogger().handlers[0].close()

    except Exception as e:
        print(e)
        logging.error("Exception occurred during closing session", exc_info=True)

        exit()


def config_device(meter_handler):

    logging.info("Configuring meter")
    
    config_status = True
    config_sequence = [
        "*CLS",
        "*RST",
        "CONF:VOLT:DC (@118,116,117,101:105,111,119,112,113,108:110,107,106)",
        "ROUTE:SCAN (@118,116,117,101:105,111,119,112,113,108:110,107,106)",
        "ROUTE:SCAN:SIZE?",
        "FORMAT:READING:CHAN ON",
        "FORMAT:READING:TIME ON",
        "TRIG:COUNT 30000",
        "TRIG:SOUR TIMER",
        "TRIG:TIMER 5",
    ]

    for command in config_sequence:
        logging.debug("Sending command {}".format(command))
        
        try:
            if command == "ROUTE:SCAN:SIZE?":
                meter_handler.write(command)
                time.sleep(DELAY)
                numberChannels = int(meter_handler.read()) + 1
            else:
                meter_handler.write(command)
                time.sleep(DELAY)

        except Exception as e:
            logging.warning("Command {} cannot be written".format(command), exc_info=True)
            config_status = False


    if config_status is True:
        logging.info("Configuration complete")
        return numberChannels

    else:
        logging.warning("Configuration incomplete")

def daq_control():

    # measure session
    visa_handler, inst_handler = open_session()
    numberChannels= config_device(meter_handler=inst_handler)

    # same datafile if True
    same_day_condition = True
    numero_dia = datetime.today().strftime('%j')
    logging.info('saving resutls in {}'.format(DATA_FILE))
    logging.info('Measuring....')

    #Leemos el dia de hoy (para que no de error)
    inst_handler.write("INIT;:SYSTEM:TIME:SCAN?")   
    print (inst_handler.read())
    points = 0
    while (points==0):
        inst_handler.write("DATA:POINTS?")
        points=int(inst_handler.read())

    #Iniciamos operación normal
    while same_day_condition:
        valores = []
        timestamp = datetime.now().strftime("%H:%M:%S")

        for chan in range(1, numberChannels):
            inst_handler.write("DATA:REMOVE? 1")
            read = inst_handler.read()
            valores.append(float(read.split(',')[0]))
            points = 0
            #wait for data
            while (points==0):
                inst_handler.write("DATA:POINTS?")
                points=int(inst_handler.read())

        multiplicadores = load_multiplicadores()
        # Aplicar multiplicadores
        valores = [valores[i] * multiplicadores[i] for i in range(len(valores))]
        valores[12] = valores[12] - 40 # Ajuste de temperatura
        #Redondear al 3er decimal
        valores = [round(num,3) for num in valores]
        valores = [str(num) for num in valores]

        # Crear la línea de salida con tabulaciones
        linea = timestamp + "\t" + "\t".join(valores) + "\n"
        # Mostrar en consola y log
        logging.info("Measured: " + timestamp)
        print(linea)
        # Guardar en el archivo
        with open(DATA_FILE, "a") as txtfile:
            txtfile.write(linea)


        if datetime.today().strftime('%j') != numero_dia:
            same_day_condition = False

    close_session(visa_handler=visa_handler, inst_handler=inst_handler)

    logging.info("Day Completed!")

if __name__ == "__main__":
    daq_control()