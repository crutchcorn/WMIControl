# Core imports
from lib.setSettings import djangopath
djangopath(up=1, settings='settings')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

# DB models and exceptions
from data import models
from machineclasses.MachineClass import Machine


class WMIMachine(Machine):
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

    def createWMICPU(self, cpu):
        archName, familyName, upgradeName, PartNumber, SerialNumber = self.lookupWMICPU(cpu)
        return self.createCPU(
            name=cpu.Name.strip(),
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

    def createWMIRAM(self, ram):
        formName, memTypeName, PartNumber, SerialNumber = self.lookupWMIRAM(ram)
        return self.createRAM(
            size=int(ram.Capacity),
            manufacturer=ram.Manufacturer,
            partnum=PartNumber,
            speed=ram.Speed,
            formFactor=formName.name,
            memoryType=memTypeName.name,
            serial=SerialNumber,
            location=ram.DeviceLocator
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

    def createWMIGPU(self, gpu):
        vidArchName, memTypeName = self.lookupWMIGPU(gpu)
        return self.createGPU(
            name=gpu.Name.strip(),
            size=int(gpu.AdapterRAM),
            refresh=gpu.MaxRefreshRate,
            arch=vidArchName,
            memoryType=memTypeName,
            location=gpu.DeviceID
        )

    def createWMILAN(self, net):
        return self.createLAN(
            name=net.Name.strip(),
            manufacturer=net.Manufacturer,
            mac=net.MACAddress,
            location=net.DeviceID
        )

    def createWMIDrive(self, disk):
        return self.createDrive(
            name=disk.Model,
            size=disk.Size,
            interface=disk.InterfaceType,
            manufacturer=disk.Manufacturer,
            serial=disk.SerialNumber,
            partitions=disk.Partitions
        )

    def createWMILogicDisk(self, disk, logicdisk):
        disktype = self.lookupWMILogicDisk(disktype=logicdisk.DriveType)
        return self.createLogicDisk(
            disk=disk,
            name=logicdisk.Name,
            mount=logicdisk.DeviceID,
            filesystem=logicdisk.FileSystem,
            size=logicdisk.Size,
            freesize=logicdisk.FreeSpace,
            disktype=disktype
        )

    def lookupWMILogicDisk(self, disktype):
        driveTypeName, createdDriveType = models.WMICodes.objects.get_or_create(code=disktype,
                                                                                identifier="DriveType",
                                                                                wmiObject="Win32_LogicalDisk")
        if createdDriveType:
            driveTypeName.machines.add(self.machine)
        return driveTypeName.name
