import serial
import time
import logging


port = '/dev/ttyACM0'  
baud_rate = 115200  

try:
    ser = serial.Serial(port, baud_rate, timeout=1)
except serial.SerialException:
    logging.error(f"Failed to connect to {port}.")
    exit()



fr_command = b'matter device factoryreset \n' 
ser.write(fr_command)
time.sleep(5)
    
ad_command = b'matter ble adv start \n'
ser.write(ad_command)
time.sleep(2)
logging.info("FactoryReset has been performed successfully")
ser.close()



