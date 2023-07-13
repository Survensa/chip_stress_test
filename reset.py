from mobly import asserts, base_test, signals, utils
import logging
from fabric import Connection
from invoke import UnexpectedExit
from abc import ABC, abstractmethod
from config import rpi_config, thread_config
import threading
import subprocess
import time

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



class Rpi(Reset):


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
        pid_val = ssh.run(command)

        pid_output = pid_val.stdout
        pid_lines = pid_output.split('\n')
        for line in pid_lines :
            if data.command in line:
                pid = line.split()[1]
                kill_command = f"kill -9 {pid}"
                ssh.run(kill_command)
            break
        logging.info("Example App has been closed")
        ssh.run(' sudo rm -rf /tmp/chip_*')
        ssh.close()

        if i:
            thread = threading.Thread(target=self.advertise)
            thread.start()


    def advertise(self):

        data = rpi_config()

        ssh = Connection(host=data.host, user=data.username , connect_kwargs={"password": data.password})
        path  = data.path
        try:
                ssh.run('cd ' + path +' && '+ data.command , hide =True, pty=False)
        except UnexpectedExit as e:
                if e.result.exited == -1:
                        None
                else:
                        raise
        ssh.close()
        logging.info('Iteration has been completed')


        return True
            

class Nordic(Reset):
     
    def reboot(self):
        #As of now the nRF52840-DK is not able to reboot
        return (self.factory_reset())
     
    def factory_reset(self):

        data = thread_config()

        if data == False:
            cmd = f'echo -e "matter device factoryreset" > {data.port}'
            subprocess.run(cmd , shell=True)

        else:
            ssh =  Connection(host=data.host, user=data.username , connect_kwargs={"password": data.password})     
            ssh.run(f'echo -e "matter device factoryreset" > {data.port}')

        time.sleep(2)

        return True
     
    def advertise(self):
        #Since the advertisement is done during factory_reset it can be skipped
        return True
