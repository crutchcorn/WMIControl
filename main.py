#!/usr/bin/env python3
"""WMIControl - For those hard to reach servers. UoNC eat your heart out

Usage:
  WMIControl scan
  WMIControl scan --subnet=<subnet>
  WMIControl scan (-r | --range) <start> <end>

Options:
  -h --help                  Show this screen.
  -v --version               Show version.
  scan                       Start a local or remote scan.       IE: When empty, local
  -r --range                 Scan a range of IP addresses.       EG: 192.168.1.1
  --subnet=<subnet>          Scan entire IP subnet.              EG: 192.168.1

"""

import csv
import json
import sys
import os

## Custom Imports
from docopt import docopt
import wmi
import nmap
import toml
import pywintypes
from integrations import assetpanda
from collections import namedtuple

## Database info
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

from django.core.wsgi import get_wsgi_application
from django.conf import settings
application = get_wsgi_application()

## DB models and exceptions
from data import models
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

## Custom Error Exceptions
class AlreadyInDB(Exception):
    """Base class for exceptions in this module."""
    pass

## NMAP Stuff
def getComputers(search):
    nm = nmap.PortScanner()
    nm.scan(hosts=search, arguments='-sn -n')
    computers = nm.all_hosts() # Gives me an array of hosts
    return computers

## WMI Stuff
def WMIInfo(c):
    B2GB = 1024 * 1024 * 1024

    # Mac Address & Network Adapter Name
    # Placed first to check if exists in database
    netdevices = filter(
        lambda net: net.MACAddress != None and net.PhysicalAdapter and net.Manufacturer != "Microsoft" and not net.PNPDeviceID.startswith("USB\\") and not net.PNPDeviceID.startswith("ROOT\\"),
        c.Win32_NetworkAdapter()
    )

    for macaddr in netdevices:
        try:
            machine = models.Machine.objects.get(network__mac=macaddr.MACAddress)
        except ObjectDoesNotExist:
            print("This item is not in the database")
            machine = models.Machine()
        except MultipleObjectsReturned:
            print("You have a duplicate machine in your database!")
            raise SystemExit
        else:
            raise AlreadyInDB

    machine.name = c.Win32_ComputerSystem()[-1].Name
    machine.manufacturer = c.Win32_ComputerSystem()[-1].Manufacturer.strip()
    machine.compModel = c.Win32_ComputerSystem()[-1].Model.strip()
    machine.cpu = models.CPU.objects.get_or_create(name = c.Win32_Processor()[0].Name.strip(), cores = c.Win32_ComputerSystem()[-1].NumberOfLogicalProcessors, count = len(c.Win32_Processor()))[0]
    machine.ram = models.RAM.objects.get_or_create(sticks = c.win32_PhysicalMemoryArray()[-1].MemoryDevices, size = round(int(c.Win32_ComputerSystem()[-1].TotalPhysicalMemory) / B2GB))[0]
    machine.save()

    # map(func, iterable):
    # for i in iterable:
    #     func(i)
    ### iterate through filter
    ### and make the iteration `hdd` in the lambda
    ## lambda x: funct(x), iterable
    ### funct will iterate through x
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

    if not c.Win32_VideoController():
        machine.gpus = [models.GPU.objects.get_or_create(name = 'Unknown')[0]]
    else:
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
        try:
            if c.Win32_Battery()[-1].BatteryStatus > 0:
                machine.compType = models.Machine.LAPTOP
        except IndexError:
            pass

    # Push
    machine.network = list(map(
        lambda net: models.Network.objects.get_or_create(
            name = net.Name.strip(),
            mac = net.MACAddress
        )[0],
        filter(
            lambda net: net.MACAddress != None,
            # net.PhysicalAdapter and ... and net.PNPDeviceID[0:3] != "USB" 
            c.Win32_NetworkAdapter()
        )
    ))

    ## Save machine
    machine.save()
    return machine

## Asset Management Functions: pushToAssetTracker
# This function will need to be made more generic to handle different AssetTrackers in
# more of an API implamentation than doing something specific to the DB. 
# This means that the LIB will be doing a bit more heavy lifting;
# but that's the goal of setting up an API like interface, isn't it?

def makeAssetFromDB():
    auth = assetpanda.getToken(config)
    machine = models.Machine.objects.last()
    network = machine.network.first()
    netlist = machine.network.all()
    hdd = machine.hdds.first()
    gpu = machine.gpus.first()
    ram = machine.ram
    cpu = machine.cpu
    concatenatedRoles = ""
    roles = machine.roles.all()
    for role in roles:
        concatenatedRoles += str(role) + '\n'

    # This is where the code will go to read from a database and put assets into ITAM solution
    namedfields = namedtuple('namedfields', ['ramsize', 'netmodel', 'ramsticks', 'model', 'cpucores', 'mac', 'roles', 'name', 'cpumodel', 'manufacturer', 'hddsize', 'gpus', 'hddfree', 'comptype'])
    fields = namedfields(ram.size, network.name, ram.sticks, machine.compModel, cpu.cores, network.mac, concatenatedRoles, machine.name, cpu.name, machine.manufacturer, hdd.size, gpu.name, hdd.free, machine.get_compType_display())
    assetpanda.makeAsset(auth, fields)


def main():
    global config
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
                for i in range(len(config['credentials']['wmi']['users'])):
                    print("Trying to connect to", ip, "with user '" + config['credentials']['wmi']['users'][i] + "'")
                    try:
                        c = wmi.WMI(str(ip), user=config['credentials']['wmi']['users'][i], password=config['credentials']['wmi']['passwords'][i])
                        WMIInfo(c)
                    except wmi.x_wmi as e:
                        print(e.com_error.excepinfo[2])
                    except AlreadyInDB:
                        print("This item is already in your database")
                        break
                    except IndexError:
                        print("Your configuration file is configured incorrectly")
                        raise SystemExit
                    else:
                        makeAssetFromDB()
                        break
        else:
            c = wmi.WMI()
            WMIInfo(c)
            makeAssetFromDB()

if __name__ == "__main__":
    main()