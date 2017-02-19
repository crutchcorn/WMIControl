# Core imports
import os

# Custom Imports
import wmi

# Local imports
from networkMngr import netDeviceTest, getComputers, getDeviceNetwork
from WMIMachineClass import WMIMachine

# Database info
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

# DB models and exceptions
from data import models
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from excepts import AlreadyInDB, SilentFail, AccessDenied

Byte2GB = 1024 * 1024 * 1024
local = wmi.WMI()

def testCredentials(computer, userLogin):
    print("Trying to connect to", computer, "with user '" + userLogin['user'] + "'")
    try:
        wmiObj = wmi.WMI(str(computer), user=userLogin['user'], password=userLogin['pass'])
    except wmi.x_wmi as e:
        # This is unfortunately the way this must be done. There is no error codes in wmi library AFAIK
        if e.com_error.excepinfo[2] == 'The RPC server is unavailable. ':
            raise EnvironmentError("Computer does not have WMI enabled")
        elif e.com_error.excepinfo[2] == 'Access is denied. ':
            raise AccessDenied("Incorrect credentials")
        else:
            raise wmi.x_wmi(e.com_error.excepinfo[2])
    else:
        return wmiObj


def getWMIObjs(users, search=getDeviceNetwork()[2], silentlyFail=False):
    """Given ip range search and list of dictionary users: Returns a list of WMIObjects
    If search is a list containing arguments for getComputers, it will pass them off properly using a splat operator
    As the splat operator is a bit of a more obscure usage in Python, I'll link the documentation for it
    https://docs.python.org/3/tutorial/controlflow.html#unpacking-argument-lists
    """
    wmiObjs = []

    if isinstance(search, list):
        computers = getComputers(*search)[0]
    else:
        computers = getComputers(search)[0]

    for ip, login in [(ip, login) for ip in computers for login in users]:
        try:
            wmiObj = testCredentials(ip, login)
        except (EnvironmentError, AccessDenied) as err:
            if silentlyFail:
                print(err)
            else:
                raise err
        except IndexError:
            raise IndexError("Config file has errors. Likely is unmatching user/password combo")
        else:
            wmiObjs.append(wmiObj)
            break
    return wmiObjs  # Return which credentials it was that worked in future. This will be a ID for the credential in DB


def WMIInfo(wmiObj=None, silentlyFail=False, skipUpdate=False):
    """Given wmiObj and bool settings silentlyFail and skipUpdate find information and store it in the database.
    wmiObj default is None. If none, the local WMI object will be used
    """
    if not wmiObj:
        wmiObj = local

    machineObj = WMIMachine()
    machineName = wmiObj.Win32_ComputerSystem()[-1].Name

    """Get a list of valid network devices to use later to find MAC in DB"""
    netDevices = list(filter(
        lambda net: netDeviceTest(net),
        wmiObj.Win32_NetworkAdapter()
    ))
    if not netDevices:
        errString = machineName + " does not have any valid network devices."
        if silentlyFail:
            raise SilentFail(errString)
        else:
            raise LookupError(errString)

    """Attempt to find machine and compModel"""
    badNetDevices = 0
    for macAddr in netDevices:
        # The following code works by doing the following: Scan each item in netDevices, continuing to play a game of
        # "What finishes first?". This will either be `ObjectDoesNotExist` on the last macAddr or `else:`, which breaks
        try:
            # To get a machine in the database with a matching MAC
            machineObj.machine = models.Network.objects.get(mac=macAddr.MACAddress).machine
        except ObjectDoesNotExist:
            # If nothing, create a new machine. Defaults as none, so we keep track for future testing
            badNetDevices += 1
        except MultipleObjectsReturned:
            errString = "You have a duplicate machine in your database!"
            if silentlyFail:
                raise SilentFail(errString)
            else:
                raise MultipleObjectsReturned(errString)
        else:
            if skipUpdate:
                raise AlreadyInDB(machineName, "is already in your database. Skipping")
            else:
                print(machineName + " will be updated in the local database")
                machineObj.model = machineObj.machine.model
                # Error handling needed if machine has no model
                machineObj.machine.name = machineName
                break  # Machine has been found and defined. Update the machine

    # Check if none of the devices were found
    if badNetDevices == len(netDevices):
        print(wmiObj.Win32_ComputerSystem()[-1].Name + " will be created in the local database")
        machineObj.model, _ = models.MachineModel.objects.get_or_create(name=machineObj.model.name,
                                                                        manufacturer=machineObj.model.manufacturer)

    """Begin info gathering of machine"""
    machineObj.machine.name = machineName
    machineObj.machine.os = wmiObj.Win32_OperatingSystem()[-1].Caption.strip()
    # Get the roles of the machine
    try:
        machineObj.machine.roles = list(map(
            lambda server: models.Role.objects.get_or_create(name=server.Name.strip())[0],
            wmiObj.Win32_ServerFeature()
        ))
    except AttributeError:
        pass  # Defaults to None

    """Begin info gathering of model"""
    machineObj.model.name = wmiObj.Win32_ComputerSystem()[-1].Model.strip()
    machineObj.model.manufacturer = wmiObj.Win32_ComputerSystem()[-1].Manufacturer.strip()
    # Get if machineType
    if machineObj.machine.roles:
        machineObj.model.compType = models.MachineModel.SERVER
    else:
        try:
            if wmiObj.Win32_Battery()[-1].BatteryStatus > 0:
                machineObj.model.compType = models.MachineModel.LAPTOP
        except IndexError:
            machineObj.model.compType = models.MachineModel.DESKTOP

    """Begin info gathering of CPU"""
    list(map(
        lambda cpu: machineObj.createWMICPU(cpu),
        list(filter(
            lambda processor: processor.ProcessorType == 3,
            wmiObj.Win32_Processor()
        ))
    ))

    """Begin info gathering of RAM"""
    list(map(
        lambda ram: machineObj.createWMIRAM(ram),
        filter(
            lambda mem: mem.TypeDetail != 4096,
            wmiObj.Win32_PhysicalMemory()
        )
    ))

    """Begin creation of Physical and Logical Disks
    Matching of Physical and Logical disks ported from:
    blogs.technet.microsoft.com/heyscriptingguy/2005/05/23/how-can-i-correlate-logical-drives-and-physical-disks/
    Thanks, ScriptingGuy1
    """
    def makeQuery(FromWinClass, DeviceID, WhereWinClass):
        return 'ASSOCIATORS OF {' + FromWinClass + '.DeviceID="' + DeviceID + '"} WHERE AssocClass = ' + WhereWinClass

    for diskdrive in wmiObj.Win32_DiskDrive():
        """Get info from Win32_LogicalDisk"""
        physDisk, _ = machineObj.createWMIDrive(diskdrive)
        partsOnDrive = makeQuery("Win32_DiskDrive", diskdrive.DeviceID, "Win32_DiskDriveToDiskPartition")
        for diskpart in wmiObj.query(partsOnDrive):
            diskPartToLogic = makeQuery("Win32_DiskPartition", diskpart.DeviceID, "Win32_LogicalDiskToPartition")
            for logicdisk in wmiObj.query(diskPartToLogic):
                """Get info from Win32_LogicalDisk"""
                machineObj.createWMILogicDisk(physDisk, logicdisk)

    """Begin creation of GPU"""
    list(map(
        lambda gpu: machineObj.createWMIGPU(gpu),
        filter(
            lambda vidCont: vidCont.AdapterRAM,
            wmiObj.Win32_VideoController()
        )
    ))

    """Begin creation of Network"""
    list(map(
        lambda net: machineObj.createWMILAN(net),
        netDevices
    ))
    machineObj.save()
    return machineObj.machine
