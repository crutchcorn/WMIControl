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

    TODO: Split off into two functions - One that tests credentials with computer, one that handles the looping"""
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
    return wmiObjs  # Return credentials that worked in future. This will be a ID for the credential in DB


def WMIInfo(wmiObj=None, silentlyFail=False, skipUpdate=False):
    """Given wmiObj and bool settings silentlyFail and skipUpdate find information and store it in the database.
    wmiObj default is None. If none, the local WMI object will be used"""
    if not wmiObj:
        wmiObj = local

    """Get a list of valid network devices to use later to find MAC in DB"""
    netdevices = list(filter(
        lambda net: netDeviceTest(net),
        wmiObj.Win32_NetworkAdapter()
    ))
    if not netdevices:
        errString = wmiObj.Win32_ComputerSystem()[-1].Name + " does not have any valid network devices."
        if silentlyFail:
            raise SilentFail(errString)
        else:
            raise LookupError(errString)

    """Setup machine and compModel to start import data into it"""
    machine, compModel = None, None
    for macaddr in netdevices:
        try:
            machine = models.Network.objects.get(mac=macaddr.MACAddress).machine  # Gets machine with mac address
        except ObjectDoesNotExist:
            machine, compModel = models.Machine(), models.MachineModel()
        except MultipleObjectsReturned:
            errString = "You have a duplicate machine in your database!"
            if silentlyFail:
                raise SilentFail(errString)
            else:
                raise MultipleObjectsReturned(errString)
        else:
            if skipUpdate:
                raise AlreadyInDB(machine.name, "is already in your database. Skipping")
            else:
                print(machine.name + " will be updated in the local database")
                compModel = machine.model  # Error handling needed if machine has no model
                break  # Machine has been found and defined. Update the machine
    # Need to add a way to make sure that a computer isn't going to replace another with matching mac
    if not machine:
        errString = "None of the network cards found have a mac address!"
        if silentlyFail:
            raise SilentFail(errString)
        else:
            raise LookupError(errString)

    """Begin creation of compModel"""
    modelName = wmiObj.Win32_ComputerSystem()[-1].Model.strip()
    modelManufacturer = wmiObj.Win32_ComputerSystem()[-1].Manufacturer.strip()
    if not machine.name:
        print(wmiObj.Win32_ComputerSystem()[-1].Name + " will be created in the local database")
        compModel, _ = models.MachineModel.objects.get_or_create(name=modelName,
                                                                 manufacturer=modelManufacturer)
    else:
        compModel.name = modelName
        compModel.manufacturer = modelManufacturer

    # The following will not only get compType, but also get the roles of the machine
    try:
        machine.roles = list(map(
            lambda server: models.Role.objects.get_or_create(name=server.Name.strip())[0],
            wmiObj.Win32_ServerFeature()
        ))
    except AttributeError:
        try:
            if wmiObj.Win32_Battery()[-1].BatteryStatus > 0:
                machine.compType = models.MachineModel.LAPTOP
        except IndexError:
            machine.compType = models.MachineModel.DESKTOP
    else:
        machine.compType = models.MachineModel.SERVER
    compModel.save()

    """Begin creation of machine"""
    machine.name = wmiObj.Win32_ComputerSystem()[-1].Name
    machine.os = wmiObj.Win32_OperatingSystem()[-1].Caption.strip()
    machine.model = compModel
    machine.save()

    """Begin creation of CPUModel"""
    def createCPU(cpu):
        try:
            PartNumber = cpu.PartNumber.strip()
        except AttributeError:
            PartNumber = None

        archName = models.WMICodes.objects.get(code=cpu.Architecture, identifier="Architecture",
                                               wmiObject="Win32_Processor")
        familyName = models.WMICodes.objects.get(code=cpu.Family, identifier="Family",
                                                 wmiObject="Win32_Processor")
        upgradeName = models.WMICodes.objects.get(code=cpu.UpgradeMethod, identifier="UpgradeMethod",
                                                  wmiObject="Win32_Processor")

        cpuMod, _ = models.CPUModel.objects.get_or_create(
            name=cpu.Name.strip(),
            manufacturer=cpu.Manufacturer,
            partnum=PartNumber,
            arch=archName.name,
            family=familyName.name,
            upgradeMethod=upgradeName.name,
            cores=cpu.NumberOfCores,
            threads=cpu.ThreadCount,
            speed=cpu.MaxClockSpeed
        )
        cpuMod.save()

        try:
            SerialNumber = cpu.SerialNumber.strip()
        except AttributeError:
            SerialNumber = None

        processor, _ = models.CPU.objects.get_or_create(
            machine=machine,
            model=cpuMod,
            serial=SerialNumber,
            location=cpu.DeviceID
        )
        processor.save()

    list(map(
        lambda cpu: createCPU(cpu),
        list(filter(
            lambda processor: processor.ProcessorType == 3,
            wmiObj.Win32_Processor()
        ))
    ))

    """Begin creation of RAM"""
    def createRAM(ram):
        try:
            PartNumber = ram.PartNumber.strip()
        except AttributeError:
            PartNumber = None

        formName = models.WMICodes.objects.get(code=ram.FormFactor, identifier="FormFactor",
                                               wmiObject="Win32_PhysicalMemory")
        memTypeName = models.WMICodes.objects.get(code=ram.MemoryType, identifier="MemoryType",
                                                  wmiObject="Win32_PhysicalMemory")

        ramMod, _ = models.RAMModel.objects.get_or_create(
            size=int(ram.Capacity),
            manufacturer=ram.Manufacturer,
            partnum=PartNumber,
            speed=ram.Speed,
            formFactor=formName.name,
            memoryType=memTypeName.name
        )
        ramMod.save()

        try:
            SerialNumber = ram.SerialNumber.strip()
        except AttributeError:
            SerialNumber = None

        ramStick, _ = models.RAM.objects.get_or_create(
            machine=machine,
            model=ramMod,
            serial=SerialNumber,
            location=ram.DeviceLocator
        )
        ramStick.save()

    list(map(
        lambda ram: createRAM(ram),
        filter(
            lambda mem: mem.TypeDetail != 4096,
            wmiObj.Win32_PhysicalMemory()
        )
    ))

    """Begin creation of Physical and Logical Disks
    Matching of Physical and Logical disks ported from:
    blogs.technet.microsoft.com/heyscriptingguy/2005/05/23/how-can-i-correlate-logical-drives-and-physical-disks/
    Thanks, ScriptingGuy1"""
    def makeQuery(FromWinClass, DeviceID, WhereWinClass):
        return 'ASSOCIATORS OF {' + FromWinClass + '.DeviceID="' + DeviceID + '"} WHERE AssocClass = ' + WhereWinClass

    def createDrive(PhysDrive):
        pdMod, _ = models.PhysicalDiskModel.objects.get_or_create(
            name=PhysDrive.Model,
            size=PhysDrive.Size,
            interface=PhysDrive.InterfaceType,
            manufacturer=PhysDrive.Manufacturer
        )
        pdMod.save()

        pd, _ = models.PhysicalDisk.objects.get_or_create(
            machine=machine,
            model=pdMod,
            serial=PhysDrive.SerialNumber,
            partitions=PhysDrive.Partitions,
        )
        pd.save()
        return pd

    for diskdrive in wmiObj.Win32_DiskDrive():
        """Get info from Win32_LogicalDisk"""
        physDisk = createDrive(diskdrive)
        partsOnDrive = makeQuery("Win32_DiskDrive", diskdrive.DeviceID, "Win32_DiskDriveToDiskPartition")
        for diskpart in wmiObj.query(partsOnDrive):
            diskPartToLogic = makeQuery("Win32_DiskPartition", diskpart.DeviceID, "Win32_LogicalDiskToPartition")
            for logicdisk in wmiObj.query(diskPartToLogic):
                """Get info from Win32_LogicalDisk"""
                driveTypeName = models.WMICodes.objects.get(code=logicdisk.DriveType, identifier="DriveType",
                                                            wmiObject="Win32_LogicalDisk")

                logicDisk, _ = models.LogicalDisk.objects.get_or_create(
                    disk=physDisk,
                    name=logicdisk.Name,
                    mount=logicdisk.DeviceID,
                    filesystem=logicdisk.FileSystem,
                    size=logicdisk.Size,
                    freesize=logicdisk.FreeSpace,
                    type=driveTypeName.name
                )
                logicDisk.save()

    """Begin creation of GPU"""
    def createGPU(gpu):
        vidArchName = models.WMICodes.objects.get(code=gpu.VideoArchitecture, identifier="VideoArchitecture",
                                                  wmiObject="Win32_VideoController")
        memTypeName = models.WMICodes.objects.get(code=gpu.VideoMemoryType, identifier="VideoMemoryType",
                                                  wmiObject="Win32_VideoController")

        gpuMod, _ = models.GPUModel.objects.get_or_create(
            name=gpu.Name.strip(),
            size=int(gpu.AdapterRAM),
            refresh=gpu.MaxRefreshRate,
            arch=vidArchName.name,
            memoryType=memTypeName.name
        )
        gpuMod.save()

        gpuCard, _ = models.GPU.objects.get_or_create(
            machine=machine,
            model=gpuMod,
            location=gpu.DeviceID,
        )
        gpuCard.save()

    list(map(
        lambda gpu: createGPU(gpu),
        filter(
            lambda vidCont: vidCont.AdapterRAM,
            wmiObj.Win32_VideoController()
        )
    ))

    """Begin creation of Network"""
    def createNetwork(net):
        netMod, _ = models.NetworkModel.objects.get_or_create(
            name=net.Name.strip(),
            manufacturer=net.Manufacturer
        )
        netMod.save()

        netCard, _ = models.Network.objects.get_or_create(
            machine=machine,
            model=netMod,
            mac=net.MACAddress,
            location=net.DeviceID,
        )
        netCard.save()

    list(map(
        lambda net: createNetwork(net),
        netdevices
    ))
    return machine
