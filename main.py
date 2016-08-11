"""WMIControl.

Usage:
  WMIControl scan
  WMIControl scan <subnet>
  WMIControl scan <start> <end>

Options:
  -h --help                     Show this screen.
  --version                     Show version.
  scan                          Start a scan          ###################### EDIT THIS WHEN YOU'RE NOT A PIECE OF SHIT
  <start>             Start of IP Range to scan.
  <end>                 End of IP Range to scan.
  --subnet=<ie: 192.168.1>      Scan entire IP subnet.

"""

#from django.core.wsgi import get_wsgi_application
#application = get_wsgi_application()

## Standard Import
#from data.models import *
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

'''
## Asset Panda
token = requests.post('https://login.assetpanda.com:443/v2/session/token', data = {'client_id':'', 'client_secret': '', 'email': '', 'password': '', 'device': '', 'app_version': ''})

key = "Bearer " + token.json()['access_token']
auth = {'Authorization':key}
print(key)

w = requests.get('https://login.assetpanda.com:443/v2/entities', headers=auth)

print(w.json())

with open('data.json', 'w') as outfile:
    json.dump(w.json(), outfile)
'''

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

    computer['os'] = c.Win32_OperatingSystem()[-1].Caption

    computer['sticks'] = c.win32_PhysicalMemoryArray()[-1].MemoryDevices

    computer['manufacturer'] = c.Win32_ComputerSystem()[-1].Manufacturer
    computer['model'] = c.Win32_ComputerSystem()[-1].Model
    computer['compname'] = c.Win32_ComputerSystem()[-1].Name
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

    '''
    for drivetype in c.Win32_DiskDrive():
        print(drivetype)
    '''

    cpusName = []
    for cpu in c.Win32_Processor():
        cpusName.append(cpu.Name)

    computer['cpusName'] = cpusName

    gpusName = []
    for gpu in c.Win32_VideoController():
        gpusName.append(gpu.Name)

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
                    netnames.add(net.Name)

    computer['macs'] = macs
    computer['netnames'] = netnames
    try:
        for server in c.Win32_ServerFeature():
            print(server) # STILL NEED TO TURN THIS INTO ACTUALLY SAVING THE INFORMATION FROM HERE SOMEPLACE. TEST SOON
            comptype = "Server"
    except:
        if c.Win32_Battery()[-1].BatteryStatus > 0:
            comptype="Laptop"
        else:
            comptype="Desktop"
    computer['comptype'] = comptype
    return computer

def main():
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
                    c = wmi.WMI(str(ip), user=r"User", password="Password")
                    WMIInfo(c)
                except wmi.x_wmi as e:
                    print("Sorry, was unable to connect.\n\tError: " + str(e))
        else:
            c = wmi.WMI()
            print(WMIInfo(c))

if __name__ == "__main__":
    main()