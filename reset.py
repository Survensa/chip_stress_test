from mobly import asserts, base_test, signals, utils
import logging
from fabric import Connection
from invoke import UnexpectedExit
from abc import ABC, abstractmethod
from config import config_data
import threading

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
        
        data = config_data()
        
        ssh = Connection(host=data['host'], user=data['username'] , connect_kwargs={"password": data['password']})
        
        reboot_command = f"sudo reboot"

        ssh.run(reboot_command)

        return True


        
        
    def factory_reset(self, i):
        
             
        data = config_data()
        
        ssh = Connection(host=data['host'], user=data['username'] , connect_kwargs={"password": data['password']})
        
        # Execute 'ps aux | grep process_name' command to find the PID
        command = f"ps aux | grep ./chip-all-clusters-app"
        pid_val = ssh.run(command)

        pid_output = pid_val.stdout
        pid_lines = pid_output.split('\n')
        for line in pid_lines :
            if './chip-all-clusters-app' in line:
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

        data = config_data()

        ssh = Connection(host=data['host'], user=data['username'] , connect_kwargs={"password": data['password']})
        path  = data['path']
        try:
                ssh.run('cd ' + path +' && ./chip-all-clusters-app ' , hide =True, pty=False)
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
        return super().reboot()
     
    def factory_reset(self):
        return super().factory_reset()
     
    def advertise(self):
        return super().advertise()
