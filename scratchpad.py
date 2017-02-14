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


class Machine:
    # Constructor
    def __init__(self, machine=models.Machine(), model=models.MachineModel(), cpu_model=models.CPUModel(),
                 processor=models.CPU(), ram_model=models.RAMModel(), ram_stick=models.RAM(),
                 gpu_model=models.GPUModel(), gpu_card=models.GPU(),
                 network_model=models.NetworkModel(), network_card=models.Network()):
        self.machine = machine
        self.model = model
        self.cpu_model = cpu_model
        self.processor = processor
        self.ram_model = ram_model
        self.ram_stick = ram_stick
        self.gpu_model = gpu_model
        self.gpu_card = gpu_card
        self.network_model = network_model
        self.network_card = network_card

    def save(self):
        self.model.save()
        self.machine.save()

    def createCPU(self, name, machine, manufacturer, arch, partnum=None, family=None, upgradeMethod=None, cores=None,
                  threads=None, speed=None, serial=None, location=None):
        self.cpu_model, _ = models.CPUModel.objects.get_or_create(
            name=name,
            manufacturer=manufacturer,
            partnum=partnum,
            arch=arch,
            family=family,
            upgradeMethod=upgradeMethod,
            cores=cores,
            threads=threads,
            speed=speed

        )

        self.processor, _ = models.CPU.objects.get_or_create(
            machine=machine,
            model=self.cpu_model,
            serial=serial,
            location=location
        )

    @staticmethod
    def lookupWMICPU(cpu):
        archName = models.WMICodes.objects.get(code=cpu.Architecture, identifier="Architecture",
                                               wmiObject="Win32_Processor")
        familyName = models.WMICodes.objects.get(code=cpu.Family, identifier="Family",
                                                 wmiObject="Win32_Processor")
        upgradeName = models.WMICodes.objects.get(code=cpu.UpgradeMethod, identifier="UpgradeMethod",
                                                  wmiObject="Win32_Processor")
        try:
            PartNumber = cpu.PartNumber.strip()
        except AttributeError:
            PartNumber = None
        try:
            SerialNumber = cpu.SerialNumber.strip()
        except AttributeError:
            SerialNumber = None
        return archName, familyName, upgradeName, PartNumber, SerialNumber

    def createWMICPU(self, cpu, machine):
        archName, familyName, upgradeName, PartNumber, SerialNumber = self.lookupWMICPU(cpu)
        self.createCPU(
            name=cpu.Name.strip(),
            machine=machine,
            manufacturer=cpu.Manufacturer,
            partnum=PartNumber,
            arch=archName.name,
            family=familyName.name,
            upgradeMethod=upgradeName.name,
            cores=cpu.NumberOfCores,
            threads=cpu.ThreadCount,
            speed=cpu.MaxClockSpeed,
            serial=SerialNumber,
            location=cpu.DeviceID
        )

    def createRAM(self, size, machine, manufacturer=None, partnum=None, speed=None, formFactor=None, memoryType=None,
                  serial=None, location=None):
        self.ram_model, _ = models.RAMModel.objects.get_or_create(
            size=size,
            machine=machine,
            manufacturer=manufacturer,
            partnum=partnum,
            speed=speed,
            formFactor=formFactor,
            memoryType=memoryType
        )

        self.ram_stick, _ = models.RAM.objects.get_or_create(
            machine=machine,
            model=self.ram_model,
            serial=serial,
            location=location
        )

    @staticmethod
    def lookupWMIRAM(ram):
        formName = models.WMICodes.objects.get(code=ram.FormFactor, identifier="FormFactor",
                                               wmiObject="Win32_PhysicalMemory")
        memTypeName = models.WMICodes.objects.get(code=ram.MemoryType, identifier="MemoryType",
                                                  wmiObject="Win32_PhysicalMemory")
        try:
            PartNumber = ram.PartNumber.strip()
        except AttributeError:
            PartNumber = None
        try:
            SerialNumber = ram.SerialNumber.strip()
        except AttributeError:
            SerialNumber = None
        return formName, memTypeName, PartNumber, SerialNumber

    def createWMIRAM(self, ram, machine):
        formName, memTypeName, PartNumber, SerialNumber = self.lookupWMIRAM(ram)
        self.createRAM(
            size=int(ram.Capacity),
            manufacturer=ram.Manufacturer,
            partnum=PartNumber,
            speed=ram.Speed,
            formFactor=formName.name,
            memoryType=memTypeName.name,
            machine=machine,
            serial=SerialNumber,
            location=ram.DeviceLocator
        )

    def createGPU(self, name, machine, size=None, refresh=None, arch=None, memoryType=None, location=None):
        self.gpu_model, _ = models.GPUModel.objects.get_or_create(
            name=name,
            size=size,
            refresh=refresh,
            arch=arch,
            memoryType=memoryType
        )

        self.gpu_card, _ = models.GPU.objects.get_or_create(
            machine=machine,
            model=self.gpu_model,
            location=location,
        )

    @staticmethod
    def lookupWMIGPU(gpu):
        vidArchName = models.WMICodes.objects.get(code=gpu.VideoArchitecture, identifier="VideoArchitecture",
                                                  wmiObject="Win32_VideoController")
        memTypeName = models.WMICodes.objects.get(code=gpu.VideoMemoryType, identifier="VideoMemoryType",
                                                  wmiObject="Win32_VideoController")
        return vidArchName.name, memTypeName.name

    def createWMIGPU(self, gpu, machine):
        vidArchName, memTypeName = self.lookupWMIGPU(gpu)
        self.createGPU(
            name=gpu.Name.strip(),
            size=int(gpu.AdapterRAM),
            refresh=gpu.MaxRefreshRate,
            arch=vidArchName,
            memoryType=memTypeName,
            machine=machine,
            location=gpu.DeviceID
        )

    def createLAN(self, name, machine, mac, manufacturer=None, location=None):
        self.network_model, _ = models.NetworkModel.objects.get_or_create(
            name=name,
            manufacturer=manufacturer
        )

        self.network_card, _ = models.Network.objects.get_or_create(
            machine=machine,
            model=self.network_model,
            mac=mac,
            location=location,
        )

    def createWMILAN(self, net, machine):
        self.createLAN(
            name=net.Name.strip(),
            manufacturer=net.Manufacturer,
            machine=machine,
            mac=net.MACAddress,
            location=net.DeviceID
        )