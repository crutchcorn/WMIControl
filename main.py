#!/usr/bin/env python3
"""WMIControl.

Usage:
  WMIControl scan
  WMIControl scan --subnet=<subnet>
  WMIControl scan (-r | --range) <start> <end>

Options:
  -h --help                  Show this screen.
  -v --version               Show version.
  scan                       Start a local or remote scan.       IE: When empty, local
  <start>                    Start of IP Range to scan.          EG: 192.168.1.1
  <end>                      End of IP Range to scan.            EG: 192.168.1.255
  --subnet=<subnet>          Scan entire IP subnet.              EG: 192.168.1

"""

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
import pywintypes

## Database info
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

from django.core.wsgi import get_wsgi_application
from django.conf import settings
application = get_wsgi_application()

## DB models and exceptions
from data import models
from django.core.exceptions import ObjectDoesNotExist

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

    key = token.json()['token_type'].title() + " " + token.json()['access_token']
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
    B2GB = 1024 * 1024 * 1024

    machine = models.Machine()

    # Mac Address & Network Adapter Name
    # Placed first to check if exists in database
    netdevices = filter(
        lambda net: net.PhysicalAdapter and net.Manufacturer != "Microsoft" and net.PNPDeviceID[0:3] != "USB",
        c.Win32_NetworkAdapter()
    )

    for macaddr in netdevices:
        try:
            get = models.Network.objects.get(mac=macaddr.MACAddress)
        except ObjectDoesNotExist:
            print("This item is not in the database")
        else:
            print("This item IS in the database")
            return

    machine.name = c.Win32_ComputerSystem()[-1].Name
    machine.manufacturer = c.Win32_ComputerSystem()[-1].Manufacturer.strip()
    machine.compModel = c.Win32_ComputerSystem()[-1].Model.strip()
    machine.cpu = models.CPU.objects.get_or_create(name = c.Win32_Processor()[0].Name.strip(), cores = c.Win32_ComputerSystem()[-1].NumberOfLogicalProcessors, count = len(c.Win32_Processor()))[0]
    machine.ram = models.RAM.objects.get_or_create(sticks = c.win32_PhysicalMemoryArray()[-1].MemoryDevices, size = round(int(c.Win32_ComputerSystem()[-1].TotalPhysicalMemory) / B2GB))[0]
    machine.save()

    # def map(func, iterable):
    # for i in iterable:
    #     yield func(i)
    # hdd becomes `i in iterable`
    machine.hdds = list(map(
        lambda hdd: models.HDD.objects.get_or_create(
            name = hdd.DeviceID,
            size = round(int(hdd.Size) / B2GB),
            free = round(int(hdd.FreeSpace) / B2GB)
        )[0],
        filter(
            lambda hdd: hdd.DriveType == 3,
            c.Win32_LogicalDisk()
        )
    ))

    machine.gpus = list(map(
        lambda gpu: models.GPU.objects.get_or_create(
            name = gpu.Name.strip()
        )[0],
        c.Win32_VideoController()
    ))

    machine.os = c.Win32_OperatingSystem()[-1].Caption.strip()

    # Get roles and computer type
    try:
        machine.roles = list(map(
            lambda server: models.Role.objects.get_or_create(name = server.Name.strip())[0],
            c.Win32_ServerFeature()
        ))
        machine.compType = models.Machine.SERVER
    except:
        if c.Win32_Battery()[-1].BatteryStatus > 0:
            machine.compType = models.Machine.LAPTOP

    # Push
    machine.network = list(map(
        lambda net: models.Network.objects.create(
            name = net.Name.strip(),
            mac = net.MACAddress
        ),
        filter(
            lambda net: net.PhysicalAdapter and net.Manufacturer != "Microsoft" and net.PNPDeviceID[0:3] != "USB",
            c.Win32_NetworkAdapter()
        )
    ))

    ## Save machine
    machine.save()
    return machine

def main():
    ## Get config file ready to roll
    with open("conf.toml") as conffile:
        config = toml.loads(conffile.read())

    ## Grab CLI Arguments
    arguments = docopt(__doc__, version='WMIControl 0.1')

    ## Let the fun (parsing) begin
    if (arguments["scan"]):
        if (arguments["--subnet"] or arguments["-r"]):
            if (arguments["--subnet"]):
                search = arguments["--subnet"]
                if search[-1] == '.':
                    search = search[:-1]
                n = search.count('.')
                for _ in range(n, 2): # xxx.xxx.xxx.xxx
                    search += ".0-255"
                search += ".1-255"
            elif (arguments["-r"] or arguments["--range"]):
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