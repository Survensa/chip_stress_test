from fabric import Connection
import time 
import logging
import os
import json
import subprocess

def thread_reset(data):


   local_file_path = os.path.abspath(os.getcwd()) + '/thread.py'

   remote_file_path = data['path']


   ssh = Connection(host=data['host'], user=data['user'] , connect_kwargs={"password": data['password']})

   ssh.put(local_file_path, remote_file_path)

   time.sleep(5)

   ssh.run(f'python3 ' + remote_file_path+ '/thread.py')


   ssh.run(f'rm '+remote_file_path+'/thread.py')

   ssh.close()

   srpdisable = 'docker exec -ti otbr ot-ctl srp server disable'
   subprocess.run(srpdisable , shell=True)
   time.sleep(1)
   srpenable = 'docker exec -ti otbr ot-ctl srp server enable'
   subprocess.run(srpenable , shell=True)

   logging.info("Completed the reset")





