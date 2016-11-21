"""WMIControl - For those hard to reach servers. UoNC eat your heart out

Usage:
  WMIControl scan
  WMIControl scan <nmapIP>
  WMIControl scan (-s | --subnet)
  WMIControl scan --finish=<iprange>
  WMIControl scan (-r | --range) <start> <end>
  WMIControl scan updatedb

Options:
  -h --help                  Show this screen
  -v --version               Show version
  scan                       Start a local or remote scan        IE: When empty, local
  <nmapIP>                   A valid nmap IP query to call       EG: 192.168.1.1/24
  -s --subnet                Scan through the entire subnet
  -r --range                 Scan a range of IP addresses        EG: 192.168.1.1
  --finish=<iprange>         Replace empty spaces with [0-255]   EG: 192.168.1
  updatedb                   Update the local DB with cloud IDs

"""

import sys
import os

## Custom Imports
from docopt import docopt
import wmi
import nmap
import toml
from integrations import assetpanda #! Replace with plugin
from netaddr import IPNetwork

## Database info
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

from django.core.wsgi import get_wsgi_application
from django.conf import settings
application = get_wsgi_application()

## DB models and exceptions
from data import models
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import IntegrityError

## This is a quick test to be used with filter() to see if a network device is a physical adapter or not
netDeviceTest = lambda net: net.MACAddress != None and net.PhysicalAdapter and net.Manufacturer != "Microsoft" and not net.PNPDeviceID.startswith("USB\\") and not net.PNPDeviceID.startswith("ROOT\\")

## Custom Error Exceptions
class AlreadyInDB(Exception):
    """Base class for exceptions in this module."""
    pass

## NMAP Stuff
def getComputers(search):
    nm = nmap.PortScanner()
    nm.scan(hosts=search, arguments='-sS -p 22 -n -T5') # Remove -n to get DNS NetBIOS results
    computers = nm.all_hosts() # Gives me an array of hosts
    return computers

## WMI Stuff
def WMIInfo(c):
    B2GB = 1024 * 1024 * 1024

    # Mac Address & Network Adapter Name
    # Placed first to check if exists in database
    netdevices = list(filter(
        lambda net: netDeviceTest(net),
        c.Win32_NetworkAdapter()
    ))

    if not netdevices:
        if config['settings']['silentlyFail']:
            return
        else:
            raise LookupError(c.Win32_ComputerSystem()[-1].Name + " does not have any network devices. Please advice")

    for macaddr in netdevices:
        try:
            machine = models.Machine.objects.get(network__mac=macaddr.MACAddress)
        except ObjectDoesNotExist:
            machine = models.Machine()
        except MultipleObjectsReturned:
            if config['settings']['silentlyFail']:
                print("You have a duplicate machine in your database")
                return
            else:
                raise MultipleObjectsReturned("You have a duplicate machine in your database!")
        else:
            break
    if machine.name: # Add option to skip asset update
        if config['settings']['skipUpdate']:
            raise AlreadyInDB(machine.name, "is already in your database. Skipping")
        else:
            print("This item will be updated in the local database")
    else:
        print("This item will be created in the local database")

    machine.name = c.Win32_ComputerSystem()[-1].Name
    machine.manufacturer = c.Win32_ComputerSystem()[-1].Manufacturer.strip()
    machine.compModel = c.Win32_ComputerSystem()[-1].Model.strip()
    machine.cpu = models.CPU.objects.get_or_create(name = c.Win32_Processor()[0].Name.strip(), cores = c.Win32_ComputerSystem()[-1].NumberOfLogicalProcessors, count = len(c.Win32_Processor()))[0]
    machine.ram = models.RAM.objects.get_or_create(sticks = c.win32_PhysicalMemoryArray()[-1].MemoryDevices, size = round(int(c.Win32_ComputerSystem()[-1].TotalPhysicalMemory) / B2GB))[0]
    try:
        machine.save() # Only use try if you want to allow script to continue running after import has failed
    except IntegrityError as err:
        if config['settings']['silentlyFail']:
            print(machine.name + " failed to import.")
            print(err)
            return
        else:
            raise IntegrityError(err)

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
    except:
        try:
            if c.Win32_Battery()[-1].BatteryStatus > 0:
                machine.compType = models.Machine.LAPTOP
        except IndexError:
            pass # The default for compType is already desktop
    else:
        machine.compType = models.Machine.SERVER

    # Push network devices to machine finally
    machine.network = list(map(
        lambda net: models.Network.objects.get_or_create(
            name = net.Name.strip(),
            mac = net.MACAddress
        )[0],
        netdevices
    ))

    ## Save machine
    machine.save()
    return machine

def makeAllAssets():
    for machine in models.Machine.objects.all().filter(cloudID=None):
        print(machine.name + " will now be added to the asset tracker")
        assetReply = assetpanda.makeAsset(machine, auth) #! Replace with plugin
        if assetReply:
            machine.cloudID = assetReply
            machine.save()

def main():
    ## Grab CLI Arguments
    arguments = docopt(__doc__, version='WMIControl 0.1')

    ## Get config file ready to roll
    with open("conf.toml") as conffile:
        config = toml.loads(conffile.read())

        # As far as I know, this is the only way to do this because of the way we will be using the plugin system. If anyone has any suggestions, please tell me
        auth = assetpanda.getToken(config) #! Replace with plugin

        ## Let the fun (parsing) begin
        if arguments["scan"]:
            local = wmi.WMI()
            if arguments["--finish"] or arguments["--range"] or arguments["<nmapIP>"] or arguments["--subnet"]:
                if arguments["--finish"]:
                    search = arguments["--finish"]
                    if search[-1] == '.':
                        search = search[:-1]
                    n = search.count('.')
                    for _ in range(n, 2): # xxx.xxx.xxx.xxx
                        search += ".0-255"
                    search += ".1-255"
                elif arguments["--range"]:
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
                elif arguments["<nmapIP>"]:
                    search = arguments["<nmapIP>"]
                elif arguments["--subnet"]:
                    validNetworkIDs = list(map(
                            lambda a: a.Index,
                            filter(
                                lambda net: net.NetEnabled == True and netDeviceTest(net),
                                local.Win32_NetworkAdapter()
                            )
                        ))
                    netDevices = []
                    for netAdapter in [netAdapter for netAdapter in local.Win32_NetworkAdapterConfiguration() if (netAdapter.Index in validNetworkIDs)]:
                        netDevices.append(netAdapter)
                    if len(netDevices) > 1:
                        i = 1
                        print("There are more than one network devices currently active")
                        print("Please select a device from the list given:")
                        for possibleNet in netDevices:
                            print(str(i) + ") " + possibleNet.Description)
                            i += 1
                        print("")
                        while True:
                            try:
                                netSelection = int(input('Input: '))
                                netDevices = [netDevices[netSelection - 1]]
                            except ValueError:
                                print("Not a number")
                            except IndexError:
                                print("Out of range number, try again")
                            else:
                                break
                    search = str(IPNetwork(netDevices[0].IPAddress[0]+"/"+netDevices[0].IPSubnet[0]).cidr)
                for ip in getComputers(search):
                    for i in range(len(config['credentials']['wmi']['users'])):
                        print("Trying to connect to", ip, "with user '" + config['credentials']['wmi']['users'][i] + "'")
                        try:
                            c = wmi.WMI(str(ip), user=config['credentials']['wmi']['users'][i], password=config['credentials']['wmi']['passwords'][i])
                            WMIInfo(c)
                        except wmi.x_wmi as e:
                            if(e.com_error.excepinfo[2] == 'The RPC server is unavailable. '): # This is unfornutately the way this must be done. There is no error codes in wmi library AFAIK
                                print("Computer does not have WMI enabled")
                                break
                            else:
                                print(e.com_error.excepinfo[2])
                        except AlreadyInDB as inDBErr:
                            print(inDBErr)
                            break
                        except IndexError:
                            raise IndexError("Your configuration file is configured incorrectly")
                        else:
                            break
            else:
                WMIInfo(local)
            # makeAllAssets() # Uncomment me
        elif arguments["updatedb"]:
            for machine in models.Machine.objects.all():
                machine.cloudID = assetpanda.getMachineAssetID(machine.network.first().mac, auth) #! Replace with plugin
                machine.save()

if __name__ == "__main__":
    main()