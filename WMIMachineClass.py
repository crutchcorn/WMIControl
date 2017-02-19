# Core imports
import os

# Database info
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

# DB models and exceptions
from data import models
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from excepts import AlreadyInDB, SilentFail, AccessDenied
from MachineClass import Machine


class WMIMachine(Machine):
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

    def lookupWMICPU(self, cpu):
        archName, createdArch = models.WMICodes.objects.get_or_create(code=cpu.Architecture, identifier="Architecture",
                                                                      wmiObject="Win32_Processor")
        familyName, createdFamily = models.WMICodes.objects.get_or_create(code=cpu.Family, identifier="Family",
                                                                          wmiObject="Win32_Processor")
        upgradeName, createdUpgrade = models.WMICodes.objects.get_or_create(code=cpu.UpgradeMethod,
                                                                            identifier="UpgradeMethod",
                                                                            wmiObject="Win32_Processor")
        if createdArch:
            archName.machines.add(self.machine)
        if createdFamily:
            familyName.machines.add(self.machine)
        if createdUpgrade:
            upgradeName.machines.add(self.machine)
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

    def lookupWMIRAM(self, ram):
        formName, createdForm = models.WMICodes.objects.get_or_create(code=ram.FormFactor, identifier="FormFactor",
                                                                      wmiObject="Win32_PhysicalMemory")
        memTypeName, createdMemType = models.WMICodes.objects.get_or_create(code=ram.MemoryType,
                                                                            identifier="MemoryType",
                                                                            wmiObject="Win32_PhysicalMemory")
        if createdForm:
            formName.machines.add(self.machine)
        if createdMemType:
            memTypeName.machines.add(self.machine)

            # Clean data and test if exists all at once. WMI returns some weird stuff, don't judge
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

    def lookupWMIGPU(self, gpu):
        vidArchName, createdVidArch = models.WMICodes.objects.get_or_create(code=gpu.VideoArchitecture,
                                                                            identifier="VideoArchitecture",
                                                                            wmiObject="Win32_VideoController")
        memTypeName, createdMemType = models.WMICodes.objects.get_or_create(code=gpu.VideoMemoryType,
                                                                            identifier="VideoMemoryType",
                                                                            wmiObject="Win32_VideoController")
        if createdVidArch:
            vidArchName.machines.add(self.machine)
        if createdMemType:
            memTypeName.machines.add(self.machine)
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