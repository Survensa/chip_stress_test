from mobly import asserts, base_test, signals, utils
import logging
from fabric import Connection
from invoke import UnexpectedExit
import invoke.exceptions
from abc import ABC, abstractmethod
from config import rpi_config, thread_config
import threading
import subprocess
import time
import os
import serial
import sys

class Reset (ABC):

    @abstractmethod
    def reboot(self):
        pass

    @abstractmethod
    def factory_reset(self):
        pass

    @abstractmethod
    def advertise(self):
        pass

    @abstractmethod
    def start_logging(self):
        pass

    @abstractmethod
    def stop_logging(self):
        pass


    
class Rpi(Reset):

    count = 0

    def reboot(self):
        
        data = rpi_config()
        
        ssh = Connection(host=data.host, user=data.username , connect_kwargs={"password": data.password})
        
        reboot_command = f"sudo reboot"

        ssh.run(reboot_command)

        return True

      
    def factory_reset(self, i):
                
        data = rpi_config()
        
        ssh = Connection(host=data.host, user=data.username , connect_kwargs={"password": data.password})
        
        # Executing the  'ps aux | grep process_name' command to find the PID value to kill
        command = f"ps aux | grep {data.command}"
        pid_val = ssh.run(command, hide = True)

        pid_output = pid_val.stdout
        pid_lines = pid_output.split('\n')
        for line in pid_lines :
            if data.command in line:
                pid = line.split()[1]
                conformance = line.split()[7]  
                if conformance == 'Ssl':             
                    kill_command = f"kill -9 {pid}"
                    ssh.run(kill_command)
            
        logging.info("Example App has been closed")
        
        ssh.close()

        if i:
            thread = threading.Thread(target=self.advertise)
            thread.start()

        time.sleep(10)        


    def advertise(self):

        logging.info("advertising the DUT")


        data = rpi_config()

        ssh = Connection(host=data.host, user=data.username , connect_kwargs={"password": data.password})
        path  = data.path
        ssh.run(' sudo rm -rf /tmp/chip_*')

        try:
                log = ssh.run('cd ' + path +' && '+ data.command , warn=True, hide =True, pty=False)
        except UnexpectedExit as e:
                if e.result.exited == -1:
                        None
                else:
                        raise

        self.start_logging(log)
        ssh.close()
        logging.info('Iteration has been completed')


        return True
    
    def start_logging(self, log):
        
        log_file = "TC_PairUnpair_log.txt"        

        if Rpi.count:
            with open(log_file, 'a') as l:
                l.write(f" \n\n  Dut log of {Rpi.count} iteration \n")
                l.write(log.stdout)

        Rpi.count += 1

        return True
    
    def stop_logging(self):

        #As we are killing the example while factory reset this will stop the logging process
        return (self.factory_reset(0))
            

class Nordic(Reset):
     
    def reboot(self):
        #As of now the nRF52840-DK is not able to reboot
        return (self.factory_reset())
     
    def factory_reset(self,i):

        data = thread_config()

        if data.host == None:
            Serial_port().write_cmd()


        else:
            ssh =  Connection(host=data.host, user=data.username , connect_kwargs={"password": data.password}) 
            for i in range(1,4) :   
                ssh.run(f'echo "matter device factoryreset" > {data.port}')

        time.sleep(2)

        if i == 0:
            self.stop_logging()

        return True
     
    def advertise(self):
        #Since the advertisement is done during factory_reset it can be skipped
        logging.info("advertising the DUT")
        return (self.factory_reset)
    
    def start_logging(self,log):

        ser = Serial_port().create_serial()

        if ser.is_open:

            log_file = "dutlog/rpi_log.txt"
            current_dir = os.getcwd()
            log_path = os.path.join(current_dir,log_file)
            if os.path.exists(log_path):
                os.remove(log_path)
    
            log = open(log_path, 'w')

            try:
                while True:
                    
                    line = ser.readline().decode('utf-8').strip()

                    if line:

                        print(line)

                        log.write(line + '\n')
                        log.flush() 

            except UnexpectedExit :

                ser.close()
                log_file.close()


        else:
            logging.info("Failed to read the log in thread")
            sys.exit()
                  
        return True
    
    def stop_logging(self):

        ser = Serial_port().create_serial()
        ser.close()

        return True
    



class Serial_port(object):
    def __init__(self) -> None:
        self.data = thread_config()

    def create_serial(self):

        con = self.data

        ser = serial.Serial(con.port, con.baudrate, timeout=1)

        if not ser.is_open:
            ser.open()

        return ser
    
    def write_cmd(self):

        port = self.data.port
        baudrate = self.data.baudrate

        try:
            ser = serial.Serial(port, baudrate, timeout=3)
        except serial.SerialException:
            logging.error(f"Failed to connect to {port}.")
            raise signals.TestAbortAll("Failed to Reset the device")
            
        cmd = b'matter device factoryreset \n' 

        for i in range(1,4):
            ser.write(cmd)
            time.sleep(2)

        ser.close()
        
def test_start(platform):

    log_file = "TC_PairUnpair_log.txt"

    if os.path.exists(log_file):
        os.remove(log_file)

    if platform == 'rpi':
        logging.info("advertising the dut")
        thread = threading.Thread(target=Rpi().advertise)
        thread.start()
        time.sleep(5)

    elif platform =='thread':
        thread = threading.Thread(target=Nordic().start_logging)
        thread.start()
        Nordic().advertise
        time.sleep(5)

    return True


def test_stop(platform):
    if platform =='rpi':
        Rpi().stop_logging()

    elif platform =='thread':
        Nordic().stop_logging()

      
    


def reset(platform, i):

    if platform == "rpi":
            Rpi().factory_reset(i)
            time.sleep(2)

    elif platform =='thread':
            Nordic().factory_reset(i)


    return True

