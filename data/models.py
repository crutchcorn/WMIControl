"""The following needs to be changed to an extreme amount. The following is how I want the DB set up:
cpu =many-to-many> uniqueCPUList =many-to-many> nonuniqueCPUModel
ram =many-to-many> uniqueRAMList =many-to-many> nonuniqueRAMStick
disk =many-to-many> uniqueDiskList =many-to-many> nonuniqueDiskModel
gpu =many-to-many> uniqueGPUList =many-to-many> nonuniqueGPUModel

And maybe, just maybe:
roles =many-to-many> uniqueRoleList =many-to-many> nonuniqueRoles

This will allow you to grab information about that model much easier, as well as have duplicates of that model

"""
from django.db import models

from macaddress.fields import MACAddressField


# from djmoney.models.fields import MoneyField

class Location(models.Model):
    campus = models.CharField(max_length=255, blank=True)
    room = models.CharField(max_length=255, blank=True)
    address = models.CharField(max_length=255, blank=True)
    computers = models.ForeignKey('Machine', null=True, blank=True)

    def __unicode__(self):
        return u"Room {}, at {}".format(self.room, self.campus)

    def __str__(self):
        return self.__unicode__()


class Machine(models.Model):
    DESKTOP = 1
    LAPTOP = 2
    SERVER = 3
    MACHINE_TYPES = (  # http://www.b-list.org/weblog/2007/nov/02/handle-choices-right-way/
        (DESKTOP, 'Desktop'),
        (LAPTOP, 'Laptop'),
        (SERVER, 'Server'),
    )
    compType = models.PositiveSmallIntegerField(
        choices=MACHINE_TYPES,
        default=DESKTOP
    )
    name = models.CharField(max_length=255, unique=True)
    manufacturer = models.CharField(max_length=255, blank=True)
    compModel = models.CharField(max_length=255, blank=True)
    os = models.CharField(max_length=255, blank=True)
    cloudID = models.PositiveSmallIntegerField(null=True, blank=True, unique=True)
    # THIS NEEDS TO BE CHANGED AS THEY ARE UNIQUE NOW
    cpu = models.ManyToManyField('CPU', blank=True)  # Many to many, as CPUs are not unique.
    # THIS NEEDS TO BE CHANGED AS THEY ARE UNIQUE NOW
    ram = models.ManyToManyField('RAM', blank=True)  # Many to many, as RAM is not unique.
    hdds = models.ManyToManyField('HDD', blank=True)
    gpus = models.ManyToManyField('GPU', blank=True)
    activation = models.OneToOneField('Activation', null=True, blank=True)  # Licences have parent-child relationship
    roles = models.ManyToManyField('Role', blank=True)  # Roles are not unique

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.__unicode__()


class CPU(models.Model):  # Add choices for Architecture, Family, UpgradeMethod
    name = models.CharField(max_length=255)
    manufacturer = models.CharField(max_length=255)
    partnum = models.CharField(max_length=255, null=True, blank=True)
    serial = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    count = models.PositiveSmallIntegerField(null=True, blank=True)
    cores = models.PositiveSmallIntegerField(null=True, blank=True)
    threads = models.PositiveSmallIntegerField(null=True, blank=True)
    speed = models.PositiveSmallIntegerField(null=True, blank=True)

    def __unicode__(self):
        return u"{}, {} Cores".format(self.name, self.cores)

    def __str__(self):
        return self.__unicode__()


class RAM(models.Model):  # Add choices for FormFactor, SMBIOSMemoryType
    size = models.BigIntegerField()
    manufacturer = models.CharField(max_length=255)
    partnum = models.CharField(max_length=255, null=True, blank=True)
    serial = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    speed = models.PositiveSmallIntegerField(null=True, blank=True)

    def sizeInGB(self):
        return int(self.size) / (1024 * 1024 * 1024)

    def sizeInMB(self):
        return int(self.size) / (1024 * 1024)

    def sizeInKB(self):
        return int(self.size) / 1024

    def __unicode__(self):
        return u"{} GB, {} Number Of Sticks".format(self.size, self.sticks)

    def __str__(self):
        return self.__unicode__()


class HDD(models.Model):  # Add/change. Must be renamed to disks
    name = models.CharField(max_length=255, blank=True)
    size = models.BigIntegerField()
    free = models.PositiveSmallIntegerField(null=True, blank=True)

    def sizeInGB(self):
        return int(self.size)/(1024 * 1024 * 1024)

    def sizeInMB(self):
        return int(self.size)/(1024 * 1024)

    def sizeInKB(self):
        return int(self.size)/1024

    def __unicode__(self):
        return u"{} Mount, {} GB, {} GB Free".format(self.name, self.size, self.free)

    def __str__(self):
        return self.__unicode__()


class GPU(models.Model):  # Add choices for VideoArchitecture, VideoMemoryType
    name = models.CharField(max_length=255)
    size = models.BigIntegerField()
    location = models.CharField(max_length=255, null=True, blank=True)
    refresh = models.PositiveSmallIntegerField(null=True, blank=True)

    def sizeInGB(self):
        return int(self.size)/(1024 * 1024 * 1024)

    def sizeInMB(self):
        return int(self.size)/(1024 * 1024)

    def sizeInKB(self):
        return int(self.size)/1024

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.__unicode__()


class Network(models.Model):
    machine = models.ForeignKey('Machine')  # One to many, network cards ARE unique and can be moved (MAC addresses)
    name = models.CharField(max_length=255, blank=True, null=True)
    mac = MACAddressField(unique=True)
    manufacturer = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return u"{}, {} Mac Address".format(self.name, self.mac)

    def __str__(self):
        return self.__unicode__()


class Activation(models.Model):
    COAID = models.CharField(max_length=255, null=True, blank=True, unique=True)
    productKey = models.CharField(max_length=255, unique=True)
    securityCode = models.CharField(max_length=255, null=True, blank=True)
    windowsVer = models.CharField(max_length=255)

    def __unicode__(self):
        return self.COAID

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
