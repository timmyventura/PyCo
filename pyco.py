
import paramiko
import time
import sys, os
import argparse
import yaml
import smtplib
from jinja2 import Environment, FileSystemLoader
import sys
import os

NEW_LINE_SYMBOL = '\n'
EXIT_COMMAND = 'exit'
DEFAULT_SLEEP_PROCESS_TIME = 1
RECEIVE_BUFFER_SIZE_BY_DEFAULT = 1000
MAX_RESPONSE_BUFFER_SIZE = 500000000
TIME_FORMAT = '%d-%H-%M-%S'
MONTH_FORMAT = '%m'
YEAR_FORMAT = '%Y'

def get_argm_from_user(): # Set arguments for running
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--configuration", dest="configuration", default = 'configuration.yaml', help="Path to configuration file")
    parser.add_argument("-l", "--log", dest="log", default = 'filename.log', help="Write paramiko logs to certain file")
    return parser.parse_args()


def disable_paging(remote_conn, terminal):
    
    remote_conn.send(terminal+NEW_LINE_SYMBOL) 
    time.sleep(DEFAULT_SLEEP_PROCESS_TIME)
    output = remote_conn.recv(RECEIVE_BUFFER_SIZE_BY_DEFAULT)
    
    return output

def close_remote_connection(remote_conn):
    remote_conn.send(EXIT_COMMAND+NEW_LINE_SYMBOL)
    remote_conn.close()	

def return_connection(ip, username, password):
    paramiko.util.log_to_file(args.log)
    remote_conn_pre = paramiko.SSHClient()
    remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    remote_conn_pre.connect(ip, timeout=5, username=username, password=password, allow_agent=False, look_for_keys=False)
    return remote_conn_pre.invoke_shell()

def run_cisco_command(remote_conn, time_to_sleep, command, terminal):
    output = remote_conn.recv(RECEIVE_BUFFER_SIZE_BY_DEFAULT)
    disable_paging(remote_conn, terminal)
    remote_conn.send(NEW_LINE_SYMBOL)
    output = remote_conn.recv(0)
    remote_conn.send(command + NEW_LINE_SYMBOL)
    time.sleep(time_to_sleep)
    return remote_conn.recv(MAX_RESPONSE_BUFFER_SIZE)

def get_filepath(root, devicename, ip):

    mytime = time.strftime(TIME_FORMAT)
    month = time.strftime(MONTH_FORMAT)
    year = time.strftime(YEAR_FORMAT)
    filename = (ip + "-" + mytime)
    return os.path.join(root, devicename, year, month, filename)


def parsing_configuration(config_file):
    try:
      with open(config_file) as f:
       templates = yaml.load(f)
    except Exception as mes:
      print('Error load configuration file. Message: {0}'.format(mes))
    else:
	  return templates
   
	
def write_to_file(root, ip, devicename, output):
   
    filepath = get_filepath(root, devicename, ip)
    if not os.path.exists(os.path.dirname(filepath)):
     os.makedirs(os.path.dirname(filepath))
    try:
      with open(filepath, "w") as f:
        f.write(output)
        f.close()
    except Exception as exc:
        print(exc)
    else:
        return filepath   

def send_notification(text, subject_type, **notifications):
    body = "\r\n".join(("From: %s" % notifications['from_host'], "To: %s" % ",".join(notifications['to_host']), "Subject: %s" % notifications['subject'][subject_type], "", text))
    server = smtplib.SMTP(notifications['server'])
    server.sendmail(notifications['from_host'], notifications['to_host'], body)
    server.quit()
	   
def template_rendering(zones, template_path):
    template_dir, template = os.path.split(template_path)
    env = Environment(loader=FileSystemLoader(template_dir), trim_blocks=True, lstrip_blocks=True)
    template = env.get_template(template)
    return template.render(zones)
	   
if __name__ == '__main__':
 
   args = get_argm_from_user()
   template = parsing_configuration(args.configuration)
   nice_zones = {'zones':{}}
   problem_zones = {'zones':{}}
   for zone in template['zones']:
       if template['zones'][zone]['active']:
         nice_devices = {'devices':[]}
         problem_devices = {'devices':[]}
         for device in template['zones'][zone]['devices']:
             if device['active']:
               try:
                 remote_conn = return_connection(device['ip'], username=template['username'], password=template['password'])
                 output = run_cisco_command(remote_conn, device['sleep'], template['command'], device['terminal'])
                 write_to_file(template['root_directory'], device['ip'], device['name'], output)
                 close_remote_connection(remote_conn)
               except Exception as exc:
                 problem_devices['devices'].append({'name': device['name'], 'status': 'Error. Message: {0}'.format(exc)})
                 continue
               else:
                 nice_devices['devices'].append({'name': device['name'], 'status': 'OK'})
         if nice_devices['devices']:
            nice_zones['zones'][zone] = nice_devices
         if problem_devices['devices']:
            problem_zones['zones'][zone] = problem_devices
   if template['notification']['active']:
      if nice_zones['zones']:			
         send_notification(template_rendering(nice_zones, template['notification']['template']), 'normal', **template['notification'])
      if problem_zones['zones']:
         send_notification(template_rendering(problem_zones, template['notification']['template']), 'error', **template['notification'])
  
 
