# to-do: 
#    set lamba
#    id by S/N (open all and check
#    id in logfile
#
#
import pyvisa  # for scpi
import time  # for sleep
import logging
import csv
import configparser
import argparse
from os import path

# INT_ID = "USB0::4883::32802::M00450923::0::INSTR"


def read_arguments():
    my_parser = argparse.ArgumentParser()
    # my_parser.version = "1.0"

    my_parser.add_argument(
        "-c",
        "--config_file",
        action="store",
        type=str,
        required=True,
        help="configuration file",
    )

    my_parser.add_argument(
        "-l",
        "--log_file",
        action="store",
        type=str,
        required=False,
        default="default.log",
        help="log file",
    )

    return my_parser.parse_args()


def open_session(log_file, serial_number):
    logging.basicConfig(
        filename=log_file,
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

        #all VISA devices (includinf serial
        all_visa_dev = visa_handler.list_resources()
        
        # USB devices
        selected_dev = [visa_id for visa_id in all_visa_dev if (('USB' in visa_id) & (serial_number in visa_id))]
       
        if selected_dev:
                
            logging.info("Openning S/N={} with VISA_ID={} ".format(serial_number,selected_dev))
            inst_handler = visa_handler.open_resource(selected_dev[0])
            time.sleep(DELAY)

            inst_handler.query_delay = DELAY
            time.sleep(DELAY)
               
            inst_handler.timeout = 1000
            time.sleep(DELAY)
            logging.info("Session and meter open ")

            return visa_handler, inst_handler
        
        else:
            logging.info("Device S/N={} in VISA_IDs={} ".format(serial_number,all_visa_dev))
            visa_handler.close()

            exit()
            
    except Exception as e:
        print(e)
        logging.error("Exception occurred during session openning", exc_info=True)

        exit()

def close_session(visa_handler, inst_handler):
    try:
        
        logging.info("Closing session")
        inst_handler.close()
        visa_handler.close()
        
        logging.info("Session closed")
        logging.getLogger().handlers[0].close()

    except Exception as e:
        print(e)
        logging.error("Exception occurred during closing session", exc_info=True)

        exit()


def config_and_check(meter_handler, initial_config_sequence, check_dict, inifile_config):

    logging.info("Session details: config ID={}, Sensor={}, Fiber={}, Comment={}"
            .format(inifile_config['ID']['ConfigId'],
                    inifile_config['Description']['Sensor'],
                    inifile_config['Description']['Fiber'],
                    inifile_config['Description']['Comment']))
    
    logging.info("Configuring meter")
    
    config_sequence = initial_config_sequence

    # meter config: Default + .ini
    config_sequence.append("SENS:CORR:WAV {}".format(inifile_config['Configuration']['Lambda']))
    config_sequence.append("SENS:CORR {}".format(inifile_config['Configuration']['Attenuation']))
 
 
    
    # configuration sequence:
    config_status = True

    for command in config_sequence:
        logging.debug("Sending command {}".format(command))

        try:
            meter_handler.write(command)
            time.sleep(DELAY)

        except Exception as e:
            logging.warning("Command {} cannot be written".format(command), exc_info=True)
            config_status = False


    if config_status is True:
        logging.info("Configuration complete")

    else:
        logging.warning("Configuration incomplete")

    # checking configuration:
  
    logging.info("Checking configuration:")
    check_results_dict = {}

    for item in check_dict.keys():
        try:
            
            check_results_dict[item] = meter_handler.query(check_dict[item])
            time.sleep(DELAY)

        except Exception as e:
            print(e)
            logging.warning(
                "Exception occurred during querying command {}".format(check_dict[item]),
                exc_info=True,
            )

            check_results_dict[item] = "ERROR"



    for item in check_results_dict.keys():
        logging.info(
                "{} ({})={}\r".format(
                item, check_dict[item], check_results_dict[item].strip()
            )
        )


# ------------------------------------------------------------
#  Fix configuratin: DELAY, CONF_SEQ, CHECK_LIST, MEAURES
# ------------------------------------------------------------

CONF_SEQ_PM103 = [
        "*RST",
        "SENS:CORR:WAV 800",
        "SENS:CURR:RANG:AUTO ON",
        "SENS:POW:RANG:AUTO ON",
        "SENS:CORR 0.0",
    ]

CHECK_DICT_PM103 = {
        "Auto test": "*TST?" ,
        "Average count": "SENS:AVER?",
        "Atenuation" : "SENS:CORR?",
        "Wavelength" : "SENS:CORR:WAV?",
        "Responsivity":"SENS:CORR:POW:PDI:RESP?",
        "Power range in auto": "SENS:POW:RANG:AUTO?",
        "Power range": "SENS:POW:RANG?",
        "Current range in auto": "SENS:CURR:RANGE:AUTO?",
        "Current range": "SENS:CURR:RANGE?",
    }

MEASURES = ["MEAS:POW?", "MEAS:CURR?"]
DELAY = 0.1



# command args reading
args = read_arguments()

# UTC time
session_initial_time = time.gmtime()

# 1 filename / each day named as %Y-%m-%d.data
data_basefilename = time.strftime("%Y-%m-%d", session_initial_time) + ".data"
measures_path = path.dirname(path.abspath(args.config_file))

data_filename = path.join(measures_path,data_basefilename)
log_filename  = path.join(measures_path,'logfile.log')


# ini file
ini_config = configparser.ConfigParser()
ini_config.read(args.config_file)


# measure session
visa_handler, inst_handler = open_session(log_file=log_filename, serial_number=ini_config['ID']['SerialNumber'])


   
config_and_check(meter_handler=inst_handler, initial_config_sequence=CONF_SEQ_PM103, check_dict=CHECK_DICT_PM103, inifile_config=ini_config)


# ---- TIME ---
# Get the current time in seconds since the epoch
# gmtime is UTC time
# dataframe headers
data_header = ["UTC"]
data_header.extend([command for command in MEASURES])

with open(data_filename, "w+", newline="") as csvfile:


    # same datafile if True
    same_day_condition = True

    # Create a CSV writer object & write header
    csv_writer = csv.writer(csvfile)
    csv_writer.writerow(data_header)
    
    logging.info('saving resutls in {}'.format(data_filename))
    logging.info('Measuring....')

 
    while same_day_condition:


        
        final_timestamp = time.mktime(time.gmtime()) + float(ini_config['Configuration']['SampleTime'])
        
        final_time = time.gmtime(final_timestamp)
        
        inst_handler.write("INIT")

        time.sleep(DELAY)

        measured_data = [
                inst_handler.query(command).strip()
                for command in MEASURES
            ]

        # Write data to the CSV file
        current_utctime = time.gmtime()

        new_csvline = [time.strftime("%H:%M:%S", current_utctime)]
        new_csvline.extend(measured_data)
        
        #ini_config['Configuration']['SampleTime']
        

        # same day
        #if final_time.tm_mday == session_initial_time.tm_mday:
        if final_time.tm_min == session_initial_time.tm_min:
            csv_writer.writerow(new_csvline)
            csvfile.flush()

        else:
            same_day_condition = False
        
        if final_time >= time.gmtime():
            time.sleep(time.mktime(final_time) - time.mktime(time.gmtime()))


close_session(visa_handler=visa_handler, inst_handler=inst_handler)

logging.info("Gute Nacht!")

exit(0)

