"""This is the Django models module.
The following how the DB is set up:
CPU =many-to-one> CPUModel
RAM =many-to-one> RAMModel
PhysicalDisk =many-to-one> PhysicalDiskModel
LogicalDisk =many-to-one> PhysicalDisk
GPU =many-to-one> GPUModel

In the future, it may also have the following pattern:
roles =many-to-many> uniqueRoleList =many-to-many> nonuniqueRoles

All of these unique models have a variable called "machine" which is a forgein key with the machine associated.
As there are both unique and non-unique identifications of each model, it will be much easier for you to grab
information about that model much easier, as well as have duplicates of that model.

vvvvv
You may turn a code into a human readable name as such:
>>> ComputerType = 0
>>> models.Machine.MACHINE_TYPES[ComputerType][1]
>>> "Desktop"
That being said, not all values start at 0. (Thanks, Microsoft)
Because of this, a new function may be introduced per table, per choice, to retreive the human readable value from code
^^^^^
The previous method must be depreciated. A new table with initial data will be introduced to help with the storing
process of data from WMI. This table will hold the following data:
NumericalResponce (int) | HumanResponce (string) | WMIVariable (string) | WMIObject (string)

For a guide on how to fill the model with initial data:
https://docs.djangoproject.com/en/1.10/howto/initial-data/

This will allow you to easily query this table from WMI to store data in the global DB as more universal codes. This
will allow shared platform setups to be easily handled.

Before I allow things to get too far, I'll need to really think about the datatypes and lengths for each field.

"""

from django.db import models
from macaddress.fields import MACAddressField
# from djmoney.models.fields import MoneyField


class WMICodes(models.Model):
    name = models.CharField(max_length=255)
    code = models.PositiveSmallIntegerField()
    identifier = models.CharField(max_length=255)
    wmiObject = models.CharField(max_length=255)

    def __unicode__(self):
        return u"\"{}\" at {}.{}".format(self.name, self.wmiObject, self.identifier)

    def __str__(self):
        return self.__unicode__()


class Location(models.Model):
    campus = models.CharField(max_length=255, blank=True)
    room = models.CharField(max_length=255, blank=True)
    address = models.CharField(max_length=255, blank=True)
    computers = models.ForeignKey('Machine', null=True, blank=True)

    def __unicode__(self):
        return u"Room {}, at {}".format(self.room, self.campus)

    def __str__(self):
        return self.__unicode__()


class MachineModel(models.Model):
    UNKNOWN = 0
    OTHER = 1
    DESKTOP = 2
    LAPTOP = 3
    SERVER = 4
    MACHINE_TYPES = (
        (UNKNOWN, 'Unknown'),
        (OTHER, 'Other'),
        (DESKTOP, 'Desktop'),
        (LAPTOP, 'Laptop'),
        (SERVER, 'Server'),
    )
    compType = models.PositiveSmallIntegerField(
        choices=MACHINE_TYPES,
        default=UNKNOWN
    )
    manufacturer = models.CharField(max_length=255, blank=True)
    name = models.CharField(max_length=255, blank=True)

    # def getCPUs(self):
    #     return list(set([machine.cpu_set.model for machine in Machine.objects.filter(model__name=self.name)]))

    # ram = models.ForeignKey('RAMModel')
    # disks = models.ForeignKey('PhysicalDiskModel')
    # gpu = models.ForeignKey('GPUModel')
    # network = models.ForeignKey('NetworkModel')

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.__unicode__()


class Machine(models.Model):
    model = models.ForeignKey('MachineModel', blank=True, null=True)
    name = models.CharField(max_length=255, unique=True)
    os = models.CharField(max_length=255, blank=True)  # Change to a seperate table of some kind
    activation = models.OneToOneField('Activation', null=True, blank=True)  # Licences have parent-child relationship
    cloudID = models.PositiveSmallIntegerField(null=True, blank=True, unique=True)
    roles = models.ManyToManyField('Role', blank=True)  # Roles are not unique

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.__unicode__()


class CPUModel(models.Model):
    name = models.CharField(max_length=255)
    manufacturer = models.CharField(max_length=255, blank=True, null=True)
    partnum = models.CharField(max_length=255, null=True, blank=True)
    arch = models.CharField(max_length=255, null=True, blank=True)
    family = models.CharField(max_length=255, null=True, blank=True)
    upgradeMethod = models.CharField(max_length=255, null=True, blank=True)
    cores = models.PositiveSmallIntegerField(null=True, blank=True)
    threads = models.PositiveSmallIntegerField(null=True, blank=True)
    speed = models.PositiveSmallIntegerField(null=True, blank=True)

    def __unicode__(self):
        return u"{}, {}".format(self.name, self.arch)

    def __str__(self):
        return self.__unicode__()


class CPU(models.Model):
    machine = models.ForeignKey('Machine')
    model = models.ForeignKey('CPUModel')
    serial = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return u"CPU {}, {}".format(self.serial, self.location)

    def __str__(self):
        return self.__unicode__()


class RAMModel(models.Model):
    size = models.BigIntegerField()
    manufacturer = models.CharField(max_length=255, blank=True, null=True)
    partnum = models.CharField(max_length=255, null=True, blank=True)
    speed = models.PositiveSmallIntegerField(null=True, blank=True)
    formFactor = models.CharField(max_length=255, null=True, blank=True)
    memoryType = models.CharField(max_length=255, null=True, blank=True)

    def sizeInGB(self):
        return int(self.size) / (1024 * 1024 * 1024)

    def sizeInMB(self):
        return int(self.size) / (1024 * 1024)

    def sizeInKB(self):
        return int(self.size) / 1024

    def __unicode__(self):
        return u"{} GB, {}".format(self.sizeInGB(), self.manufacturer)

    def __str__(self):
        return self.__unicode__()


class RAM(models.Model):
    machine = models.ForeignKey('Machine')
    model = models.ForeignKey('RAMModel')
    serial = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return u"Serial Number: {}".format(self.serial)

    def __str__(self):
        return self.__unicode__()


class PhysicalDiskModel(models.Model):
    name = models.CharField(max_length=255, blank=True)
    size = models.BigIntegerField()
    interface = models.CharField(max_length=5, blank=True)
    manufacturer = models.CharField(max_length=255, blank=True)

    def sizeInGB(self):
        return int(self.size) / (1024 * 1024 * 1024)

    def sizeInMB(self):
        return int(self.size) / (1024 * 1024)

    def sizeInKB(self):
        return int(self.size) / 1024

    def __unicode__(self):
        return u"{} Mount, {} GB".format(self.name, self.sizeInGB())

    def __str__(self):
        return self.__unicode__()


class PhysicalDisk(models.Model):
    machine = models.ForeignKey('Machine')
    model = models.ForeignKey('PhysicalDiskModel')
    serial = models.CharField(max_length=255, blank=True)
    partitions = models.PositiveSmallIntegerField(null=True, blank=True)

    def __unicode__(self):
        return u"{} Mount, {} GB".format(self.name, self.serial)

    def __str__(self):
        return self.__unicode__()


class LogicalDisk(models.Model):
    UNKNOWN = 0
    NOROOTDIRECTORY = 1
    REMOVABLEDISK = 2
    LOCALDISK = 3
    NETWORKDRIVE = 4
    COMPACTDISC = 5
    RAMDISK = 6
    DRIVE_TYPES = (
        (UNKNOWN, 'Unknown'),
        (NOROOTDIRECTORY, 'No Root Directory'),
        (REMOVABLEDISK, 'Removable Disk'),
        (LOCALDISK, 'Local Disk'),
        (NETWORKDRIVE, 'Network Drive'),
        (COMPACTDISC, 'Compact Disc'),
        (RAMDISK, 'RAM Disk'),
    )
    disk = models.ForeignKey('PhysicalDisk')
    name = models.CharField(max_length=255)
    mount = models.CharField(max_length=4, null=True, blank=True)
    filesystem = models.CharField(max_length=255, null=True, blank=True)
    size = models.BigIntegerField()
    freesize = models.BigIntegerField(null=True, blank=True)
    type = models.CharField(max_length=255, null=True, blank=True)

    def sizeInGB(self):
        return int(self.size) / (1024 * 1024 * 1024)

    def sizeInMB(self):
        return int(self.size) / (1024 * 1024)

    def sizeInKB(self):
        return int(self.size) / 1024

    def freesizeInGB(self):
        return int(self.freesize) / (1024 * 1024 * 1024)

    def freesizeInMB(self):
        return int(self.freesize) / (1024 * 1024)

    def freesizeInKB(self):
        return int(self.freesize) / 1024

    def __unicode__(self):
        return u"{} Mount, {} GB, {} GB Free".format(self.name, self.size, self.free)

    def __str__(self):
        return self.__unicode__()


class GPUModel(models.Model):
    name = models.CharField(max_length=255)
    size = models.BigIntegerField()
    refresh = models.PositiveSmallIntegerField(null=True, blank=True)
    arch = models.CharField(max_length=255)
    memoryType = models.CharField(max_length=255)

    def sizeInGB(self):
        return int(self.size) / (1024 * 1024 * 1024)

    def sizeInMB(self):
        return int(self.size) / (1024 * 1024)

    def sizeInKB(self):
        return int(self.size) / 1024

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.__unicode__()


class GPU(models.Model):
    machine = models.ForeignKey('Machine')
    model = models.ForeignKey('GPUModel')
    location = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return self.location

    def __str__(self):
        return self.__unicode__()


class NetworkModel(models.Model):
    name = models.CharField(max_length=255)
    manufacturer = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):
        return u"{}, {}".format(self.name, self.manufacturer)

    def __str__(self):
        return self.__unicode__()


class Network(models.Model):
    machine = models.ForeignKey('Machine')  # One to many, network cards ARE unique and can be moved
    model = models.ForeignKey('NetworkModel', null=True, blank=True)
    mac = MACAddressField(unique=True)
    location = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return self.mac

    def __str__(self):
        return self.__unicode__()


class Activation(models.Model):
    COAID = models.CharField(max_length=255, null=True, blank=True, unique=True)
    productKey = models.CharField(max_length=255, unique=True)
    securityCode = models.CharField(max_length=255, null=True, blank=True)
    windowsVer = models.CharField(max_length=255)

    def __unicode__(self):
        return self.windowsVer, "Licence"

    def __str__(self):
        return self.__unicode__()


class Role(models.Model):  # Add/change
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.__unicode__()

# https://github.com/django-money/django-money
# https://docs.djangoproject.com/en/1.10/ref/models/fields/#integerfield
# http://stackoverflow.com/questions/3113885/difference-between-one-to-many-many-to-one-and-many-to-many
