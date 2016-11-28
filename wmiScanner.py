# Core imports
import os

# Custom Imports
import wmi

# Local imports
from networkMngr import netDeviceTest, getComputers, getDeviceNetwork

# Database info
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

# DB models and exceptions
from data import models
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from exceptions import AlreadyInDB

Byte2GB = 1024 * 1024 * 1024

local = wmi.WMI()


def getWMIObjs(users, search=getDeviceNetwork()[2]):
    """Given ip range search and list of dictionary users: Returns a list of WMIObjects"""
    wmiObjs = []
    for ip, login in [(ip, login) for ip in getComputers(search) for login in users]:
        print("Trying to connect to", ip, "with user '" + login['user'] + "'")
        try:
            wmiObj = wmi.WMI(str(ip), user=login['user'], password=login['pass'])
        except wmi.x_wmi as e:
            # This is unfortunately the way this must be done. There is no error codes in wmi library AFAIK
            if e.com_error.excepinfo[2] == 'The RPC server is unavailable. ':
                raise EnvironmentError("Computer does not have WMI enabled")
            else:
                raise wmi.x_wmi(e.com_error.excepinfo[2])
        except IndexError:
            raise IndexError("Config file has errors. Likely is unmatching user/password combo")
        else:
            wmiObjs.append(wmiObj)
            break
    return wmiObjs  # Return credentials that worked in future. This will be a ID for the credential in DB


def WMIInfo(wmiObj=wmi.WMI(), silentlyFail=False, skipUpdate=False):
    """Given wmiObj and bool settings silentlyFail and skipUpdate find information and store it in the database"""

    # Grab list of network devices. Tested to see if MAC in DB
    netdevices = list(filter(
        lambda net: netDeviceTest(net),
        wmiObj.Win32_NetworkAdapter()
    ))

    if not netdevices:
        if silentlyFail:
            return
        else:
            raise LookupError(
                wmiObj.Win32_ComputerSystem()[-1].Name + " does not have any network devices. Please advice")

    machine = models.Machine()
    for macaddr in netdevices:
        try:
            machine = models.Machine.objects.get(network__mac=macaddr.MACAddress)
        except ObjectDoesNotExist:
            pass
        except MultipleObjectsReturned:
            if silentlyFail:
                print("You have a duplicate machine in your database")
                return
            else:
                raise MultipleObjectsReturned("You have a duplicate machine in your database!")
        else:
            break
    if machine.name:
        if skipUpdate:
            raise AlreadyInDB(machine.name, "is already in your database. Skipping")
        else:
            print(machine.name + " will be updated in the local database")
    else:
        print(wmiObj.Win32_ComputerSystem()[-1].Name + " will be created in the local database")
    machine.name = wmiObj.Win32_ComputerSystem()[-1].Name
    machine.manufacturer = wmiObj.Win32_ComputerSystem()[-1].Manufacturer.strip()
    machine.compModel = wmiObj.Win32_ComputerSystem()[-1].Model.strip()
    machine.cpu = models.CPU.objects.get_or_create(
                                                   name=wmiObj.Win32_Processor()[0].Name.strip(),
                                                   cores=wmiObj.Win32_ComputerSystem()[-1].NumberOfLogicalProcessors,
                                                   count=len(wmiObj.Win32_Processor())
                                                   )[0]
    machine.ram = models.RAM.objects.get_or_create(
                                                   sticks=wmiObj.win32_PhysicalMemoryArray()[-1].MemoryDevices,
                                                   size=round(
                                                           int(
                                                                wmiObj.Win32_ComputerSystem()[-1].TotalPhysicalMemory
                                                           ) / Byte2GB
                                                        )
                                                   )[0]
    try:
        machine.save()
    except IntegrityError as err:
        if silentlyFail:
            print(machine.name + " failed to import.")
            print(err)
            return
        else:
            raise IntegrityError(err)

    machine.hdds = list(map(
        lambda hdd: models.HDD.objects.get_or_create(
            name=hdd.DeviceID,
            size=round(int(hdd.Size) / Byte2GB),
            free=round(int(hdd.FreeSpace) / Byte2GB)
        )[0],
        filter(
            lambda hdd: hdd.DriveType == 3,
            wmiObj.Win32_LogicalDisk()
        )
    ))

    if not wmiObj.Win32_VideoController():
        machine.gpus = [models.GPU.objects.get_or_create(name='Unknown')[0]]
    else:
        machine.gpus = list(map(
            lambda gpu: models.GPU.objects.get_or_create(
                name=gpu.Name.strip()
            )[0],
            wmiObj.Win32_VideoController()
        ))

    machine.os = wmiObj.Win32_OperatingSystem()[-1].Caption.strip()

    # Get roles and computer type
    try:
        machine.roles = list(map(
            lambda server: models.Role.objects.get_or_create(name=server.Name.strip())[0],
            wmiObj.Win32_ServerFeature()
        ))
    except AttributeError:
        try:
            if wmiObj.Win32_Battery()[-1].BatteryStatus > 0:
                machine.compType = models.Machine.LAPTOP
        except IndexError:
            pass  # The default for compType is already desktop
    else:
        machine.compType = models.Machine.SERVER

    # Push network devices to machine finally
    machine.network = list(map(
        lambda net: models.Network.objects.get_or_create(
            name=net.Name.strip(),
            mac=net.MACAddress
        )[0],
        netdevices
    ))

    # Save machine
    machine.save()
    return machine
