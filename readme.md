# PyCo - python script for gathering required information from network devices. 


## Common information:

Script has been tested on Cisco devices, managed by follow os: ios-xr, ios, nxos. Script has been written in python 2.7

Script consists of the next parts:

  1) PyCo.py - main module
  2) configuration.yaml - configuration file where necessary information is described. File content is described in more detail below
  3) template.j2 - template which describing body format in smtp message. Jinja2 template format is being used


## Dependencies:  
  
Before using this script, make sure that you have the following outer dependencies:

  1) Paramiko
  2) PyYAML
  3) Jinja2
  
  
## Configuration file details:

**Disclaimer:**

`If you want to gather info like running-config, mac-table, arps and etc from network devices you need to have a user with privilege level 15. Script doesn't guarantee correct work with privilege level less than 15.
I shall have tried to implement this functionality by the next release. Thanks for understanding.`
  
Let's discuss about the structure of configuration file in detail:

1. username - username for logging to network devices
2. password - password for logging to network devices
3. command  - main command performing for all devices
4. root_directory - directory in file system, where information gathered from network devices will be stored. Script will automatically  create file and path from root directory if it doesn't exist. File path has next structure: ``` /<root_directory>/<devices_name>/<year>/<month>/<ip_address-day-time>``` 
5. notification - parameters for sending notification via smtp:
     - active - if this field is true, notification will be sent
     - server - ip-address or hostname of smtp server
     - from_host - field "FROM" in smtp message
     - to_host - list of email receivers. Receivers in this list putting into "TO" smtp field
     - subject - subject of email. There are two types of subjects: normal and error
     - template - path to template file. For more information see template.j2 file above
6. zones - all devices has been divided into zones for more convenient usage. For example: zones may be physical location (data centers or another areas) where network devices are located, or type of devices(switchers, routers, dmz and etc). I recommend you to use physical location as zones
     - zone_name - certain zone
          * active - if this field is true then command (see clause 3) will be performed for all devices at this zone
          * devices - list of devices at zone
               1. name - hostname of device
               2. ip - ip-address of device
               3. sleep - system sleep time between sending information to device and receiving it. For devices managed by ios-xr, ios, nx-os recommended time is 4 seconds. Some type of devices, for examples cisco SG300 series switches, require more time to give an answer. For this devices i recommend you to use 30 seconds sleep time interval.
               4. terminal - command for disabling paging at device's cli. This command is used when you need to get all lines without pausing
               5. active - if this field is true then command (see clause 3) will be performed for device at this zone.
	  
### Example:
``` 
   username: user
   password: password
   command: show run
   root_directory: /var/configs
   notification:
      active: true
      server: 10.10.10.10
      from_host: test@test.test
      to_host:
         - name1@domain.com
         - name2@domain.com
      subject: 
         normal: 'Backup configuration files'
         error: 'Error: connection problem'
      template: /etc/pyco/template.j2      
   zones: 
      test_lab:
        active: true
        devices:
          - name: test-lab.switch.sg300.1
            ip: 192.168.100.1
            sleep: 30
            terminal: terminal data
            active: true
          - name: test-lab.switch.sg300.2
            ip: 192.168.100.2
            sleep: 30
            terminal: terminal data
            active: true
      dmz:
        active: true
        devices:
          - name: dmz.secure.asa.1
            ip: 172.16.1.1
            sleep: 4
            terminal: terminal pager 0
            active: true   
	  
```

## Usage:

> python2.7 pyco.py -c <path_to_configuration_file>

Use 

> python2.7 pyco.py -h 

to get more information about keys


