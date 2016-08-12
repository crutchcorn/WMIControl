"""WMIControl.

Usage:
  WMIControl scan
  WMIControl scan <subnet>
  WMIControl scan <start> <end>

Options:
  -h --help                     Show this screen.
  --version                     Show version.
  scan                          Start a scan          ###################### EDIT THIS WHEN YOU'RE NOT A PIECE OF SHIT
  <start>                       Start of IP Range to scan.
  <end>                         End of IP Range to scan.
  --subnet=<ie: 192.168.1>      Scan entire IP subnet.

"""

'''
## Database stuff unfinished. Do not uncomment
from django.core.wsgi import get_wsgi_application
from django.conf import settings
settings.configure()
application = get_wsgi_application()

## Standard Import
from data.models import *
'''
import csv
import json
import getopt
import sys
import os

## Custom Imports
from docopt import docopt
import wmi
import requests
import nmap
import toml


## Asset Panda
def assetPanda(config):
    token = requests.post('https://login.assetpanda.com:443/v2/session/token', data = {
        'client_id': config['credentials']['assetpanda']['client_id'],
        'client_secret': config['credentials']['assetpanda']['client_secret'],
        'email': config['credentials']['assetpanda']['email'],
        'password': config['credentials']['assetpanda']['password'],
        'device': config['credentials']['assetpanda']['device'],
        'app_version': config['credentials']['assetpanda']['app_version']
    })

    key = "Bearer " + token.json()['access_token']
    auth = {'Authorization':key}
    print(key)

    w = requests.get('https://login.assetpanda.com:443/v2/entities', headers=auth)

    print(w.json())

    with open('data.json', 'w') as outfile:
        json.dump(w.json(), outfile)

## NMAP Stuff
def getComputers(search):
    nm = nmap.PortScanner()
    nm.scan(hosts=search, arguments='-sn -n')
    computers = nm.all_hosts() # Gives me an array of hosts
    return computers

## WMI Stuff
def WMIInfo(c):

    computer = {}
    B2GB = 1024 * 1024 * 1024

    computer['os'] = c.Win32_OperatingSystem()[-1].Caption.strip()
    computer['sticks'] = c.win32_PhysicalMemoryArray()[-1].MemoryDevices
    computer['manufacturer'] = c.Win32_ComputerSystem()[-1].Manufacturer.strip()
    computer['model'] = c.Win32_ComputerSystem()[-1].Model.strip()
    computer['compname'] = c.Win32_ComputerSystem()[-1].Name.strip()
    computer['memory'] = round(int(c.Win32_ComputerSystem()[-1].TotalPhysicalMemory) / B2GB)
    computer['cores'] = c.Win32_ComputerSystem()[-1].NumberOfLogicalProcessors

    drivesName = []
    drivesSize = []
    drivesFreeSpace = []
    for disk in c.Win32_LogicalDisk ():
          if disk.DriveType == 3: # Only hard drives
            drivesName.append(disk.DeviceID)
            drivesSize.append(round(int(disk.Size) / B2GB))
            drivesFreeSpace.append(round(int(disk.FreeSpace) / B2GB))

    computer['drivesName'] = drivesName
    computer['drivesSize'] = drivesSize
    computer['drivesFreeSpace'] = drivesFreeSpace

    cpusName = []
    for cpu in c.Win32_Processor():
        cpusName.append(cpu.Name.strip())

    computer['cpusName'] = cpusName

    gpusName = []
    for gpu in c.Win32_VideoController():
        gpusName.append(gpu.Name.strip())

    computer['gpusName'] = gpusName

    # Mac Address
    macs = set()
    netnames = set()
    wifinames = ["USB", "Bluetooth"]
    brk = False
    for net in c.Win32_NetworkAdapter():
        # Widdle it down to Ethernet only
        if "Ethernet" in str(net.AdapterType):
            array = [net.Description, net.Name, net.ProductName, net.Caption]
            for item in array:
                for wifi in wifinames:
                    # Remove list wifinames from list
                    if wifi in item:
                        brk = True
                        break
                    else:
                        pass
                if brk == True:
                    brk = False
                    break
                else:
                    macs.add(net.MACAddress)
                    netnames.add(net.Name.strip())

    computer['macs'] = macs
    computer['netnames'] = netnames
    computer['roles'] = []
    try:
        for server in c.Win32_ServerFeature():
            computer['roles'].append(server.Name.strip())
            comptype = "Server"
    except:
        if c.Win32_Battery()[-1].BatteryStatus > 0:
            comptype="Laptop"
        else:
            comptype="Desktop"
    computer['comptype'] = comptype
    return computer

def main():
    ## Get config file ready to roll
    with open("conf.toml") as conffile:
        config = toml.loads(conffile.read())

    ## Grab CLI Arguments
    arguments = docopt(__doc__, version='WMIControl 0.1')
    if (arguments["scan"]):
        if (arguments["<subnet>"] or arguments["<start>"]):
            if (arguments["<subnet>"]):
                search = arguments["<subnet>"]
                if search[-1] == '.':
                    search = search[:-1]
                n = search.count('.')
                for _ in range(n, 2): # xxx.xxx.xxx.xxx
                    search += ".0-255"
                search += ".1-255"
            elif (arguments["<start>"]):
                start = tuple(part for part in arguments["<start>"].split('.'))
                end = tuple(part for part in arguments["<end>"].split('.'))
                search = ""
                for s,e in zip(start, end):
                    if (s == e):
                        search += s
                    else:
                        search += "{0}-{1}".format(s, e) 
                    search += '.'
                search = search[:-1]
            for ip in getComputers(search):
                print("Trying to connect to", ip)
                try:
                    c = wmi.WMI(str(ip), user=config['credentials']['wmi']['user'], password=config['credentials']['wmi']['pass'])
                    WMIInfo(c)
                except wmi.x_wmi as e:
                    print("Sorry, was unable to connect.\n\tError: " + str(e.com_error.excepinfo[2]))
        else:
            c = wmi.WMI()
            print(WMIInfo(c))

if __name__ == "__main__":
    main()