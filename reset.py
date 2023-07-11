from mobly import asserts, base_test, signals, utils
from matter_testing_support import matter_test_config
import json
import logging
import subprocess
from fabric import Connection
import threading
from invoke import UnexpectedExit


class Reset ():
     
    def store_data(self):

        data ={}
        subprocess.run('ls')
        subprocess.run('pwd')

        config_file = "RPIconfig.json"
        with open(config_file, 'r') as file:
            data = json.load(file)
        print(data)
        logging.info(f"Data from {config_file} has been stored in data")
        
        return data    

    def factoryreset(self, i):

        data = self.store_data()

        conf = matter_test_config
        print(conf)

        platform = conf.platform

        if platform == 'rpi':
            return (Rpi_reset().reset(data, i))
        
        elif platform == 'thread' :
            return  None 
        
        logging.info("The specified --platform is not defiened")
        raise signals.TestAbortAll("Failed to Reset the device")



class Rpi_reset(Reset):


    def reset(self, data, i):
        print(i)
        
        ssh = Connection(host=data['host'], user=data['username'] , connect_kwargs={"password": data['password']})
        
        # Execute 'ps aux | grep process_name' command to find the PID
        command = f"ps aux | grep ./chip-all-clusters-app"
        pid_val = ssh.run(command)

        pid_output = pid_val.stdout
        pid_lines = pid_output.split('\n')
        for line in pid_lines :
            if './chip-all-clusters-app' in line:
                pid = line.split()[1]
                kill_command = f"kill -9 {pid}"1
                ssh.run(kill_command)
            break
        logging.info("Example App has been closed")
        ssh.run(' sudo rm -rf /tmp/chip_*')
        ssh.close()

        thread = threading.Thread(target=self._run, args=(data,))

        if i != matter_test_config.number_of_iterations - 1:
            
            thread.start()
            logging.info('thread completed')

    

        return True
        
        
    def _run(self, data):

            
            
            ssh = Connection(host=data['host'], user=data['username'] , connect_kwargs={"password": data['password']})
            path  = data['path']
            try:
                ssh.run('cd ' + path +' && ./chip-all-clusters-app ' , hide =True, pty=False)
            except UnexpectedExit as e:
                if e.result.exited == -1:
                        print("Command exited with -1, treating as non-error")
                else:
                        raise
            ssh.close()
            logging.info('Ilration has been completed')

            return True
            
