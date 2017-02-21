"""This Django models module defines the objects that will be created when the information is read from the database.

This database has the following Table relationships:
Machine.roles =many-to-many> Roles
    Roles are not very unique. In the future, this should be expanded to be a `ConfiguredRole =one-to-one> Roles`,
    but this works well enough for now.
CPU.model =many-to-one> CPUModel
CPU.machine =ForeignKey> Machine
    The thought behind this particular design (carried across many different components in the Database), is that you
    have a unique item that serves as the actual component assigned to a machine (so that, in many instances, you can
    have many of one component assigned to the machine; for scalability) and a model object that serves as a lookup
    table for all the information that is guaranteed to be the same (based on the fact that models contain the same set
    of data between themselves). While this might be a topic of argument, I am confident in this schema as it allows
    queries to be structured easier and disallow many mistaken inputs (either by hand or automated)
RAM.model =many-to-one> RAMModel
RAM.machine =ForeignKey> Machine
LogicalDisk.disk =many-to-one> PhysicalDisk
PhysicalDisk.machine =ForeignKey> Machine
PhysicalDisk.model =many-to-one> PhysicalDiskModel
    Adding onto the Unique=>Non-Unique aspect as before, each physical disk can have many Logical disks inside of them.
    The clever amongst you will note that logical disks can span between physical disks (IE: RAID). This is a feature
    that is yet to be implemented, but will likely be changed over soon.
GPU.model =many-to-one> GPUModel
GPU.machine =ForeignKey> Machine

You can see a visual explanation in the `data` folder labeled `designgraph.svg` (data\visualization\designgraph.svg)
(BTW, I generated this fancy little table using DbVisualizer Free with a little SVG editing)

Because WMI returns codes for certain values, I've built a table that serves as a lookup table for those codes.
That being said, because not all values start at 0 (Thanks, Microsoft), and because there are so many overlapping
codes between responses, I've handled each Object::Variable pair as a kind of key inside the Table.
The table holds the following information:
NumericalResponse (int) | HumanResponse (string) | WMIVariable (string) | WMIObject (string)
You may turn a code into a human readable name as such:
 >>> HumanResponse = models.WMICodes.objects.get(code=NumericalResponse, identifier="WMIVariable", \
 wmiObject="WMIObject")

You'll notice a distinct lack of static variables to define the data. We're storing the data in a fixture. This fixture
currently requires manual loading (using manage.py), but can be switched to an initial data loading procedure (using
fixtures and initial migration files)
For a guide on how to fill the model with initial data:
https://docs.djangoproject.com/en/1.10/howto/initial-data/

For a quick rundown on setup of initial migration files:
http://stackoverflow.com/questions/25960850/loading-initial-data-with-django-1-7-and-data-migrations

Before I allow things to get too far, I'll need to really think about the datatypes and lengths for each field, as they
have been somewhat ad hoc before now.

"""

from django.db import models
from macaddress.fields import MACAddressField
# https://github.com/django-money/django-money
# from djmoney.models.fields import MoneyField


class CalcSizeMixin:
    """The way you use this is to add the class as a parent class. This will allow you to use "InGB/InMB/inKB" at the
    end of any variable name that is of the type "Integer".
    EG: sizeInGB
    """
    scalingFactors = {'TB': 1024 ** 4, 'GB': 1024 ** 3, 'MB': 1024 ** 2, 'KB': 1024}

    # __getattr__ is called when an unknown variable is called. Self is the class itself and item is the argument
    # (variable name) passed through to the function.
    def __getattr__(self, item):
        try:
            sizeProp = item[:item.index("In")]  # Gets index for keyword "In"
            unit = item[item.index("In") + 2:]  # Pass the argument of everything past keyword
            if unit in self.scalingFactors.keys():  # Test if argument matches known units
                return int(getattr(self, sizeProp)) / self.scalingFactors[unit]  # Return the math needed
            else:
                    raise AttributeError(unit + " is not an known size unit.")  # Return error message
        except ValueError:  # Ignore (AKA Return standard error message) if any other type than one of
            pass

        # Return standard error message
        raise AttributeError("'{}' object has no attribute '{}'".format(self.__class__.__name__, item))


class WMICodes(models.Model):
    name = models.CharField(max_length=255, default='Unknown')
    code = models.PositiveSmallIntegerField()
    identifier = models.CharField(max_length=255)
    wmiObject = models.CharField(max_length=255)
    machines = models.ManyToManyField('Machine', blank=True)
    UNKNOWN = 0
    KNOWN = 1
    CUSTOM = 2
    STATUS_TYPES = (
        (UNKNOWN, 'Unknown'),
        (KNOWN, 'Known'),
        (CUSTOM, 'Custom'),
    )
    status = models.PositiveSmallIntegerField(
        choices=STATUS_TYPES,
        default=UNKNOWN
    )

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
    """compyType remains a Django choice simply because there tends to be little variation in the types of computers
    you can save. Because of this, I decided to make it a choice and not a code because:
    1. It's not part of WMI, portability is key to growth.
    2. It's better for clean data; disallowing choices that could be inconsistent with others
    """
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
    os = models.CharField(max_length=255, blank=True)  # Change to a separate table of some kind
    activation = models.OneToOneField('Activation', null=True, blank=True)  # Licences have parent-child relationship
    cloudID = models.PositiveSmallIntegerField(null=True, blank=True, unique=True)
    roles = models.ManyToManyField('Role', blank=True)  # Roles are not unique

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.__unicode__()


class CPUModel(models.Model):
    name = models.CharField(max_length=255)
    manufacturer = models.CharField(max_length=255)
    arch = models.CharField(max_length=255)
    partnum = models.CharField(max_length=255, null=True, blank=True)
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


class RAMModel(models.Model, CalcSizeMixin):
    size = models.BigIntegerField()
    manufacturer = models.CharField(max_length=255, blank=True, null=True)
    partnum = models.CharField(max_length=255, null=True, blank=True)
    speed = models.PositiveSmallIntegerField(null=True, blank=True)
    formFactor = models.CharField(max_length=255, null=True, blank=True)
    memoryType = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return u"{} GB, {}".format(self.sizeInGB, self.manufacturer)

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


class PhysicalDiskModel(models.Model, CalcSizeMixin):
    name = models.CharField(max_length=255, blank=True)
    size = models.BigIntegerField()
    interface = models.CharField(max_length=5, blank=True)
    manufacturer = models.CharField(max_length=255, blank=True)

    def __unicode__(self):
        return u"{} Mount, {} GB".format(self.name, self.sizeInGB)

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


class LogicalDisk(models.Model, CalcSizeMixin):
    disk = models.ForeignKey('PhysicalDisk')
    name = models.CharField(max_length=255)
    mount = models.CharField(max_length=4, null=True, blank=True)
    filesystem = models.CharField(max_length=255, null=True, blank=True)
    size = models.BigIntegerField()
    freesize = models.BigIntegerField(null=True, blank=True)
    type = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return u"{} Mount, {} GB, {} GB Free".format(self.name, self.sizeInGB, self.freesizeInGB)

    def __str__(self):
        return self.__unicode__()


class GPUModel(models.Model, CalcSizeMixin):
    name = models.CharField(max_length=255)
    size = models.BigIntegerField(null=True, blank=True)
    refresh = models.PositiveSmallIntegerField(null=True, blank=True)
    arch = models.CharField(max_length=255, null=True, blank=True)
    memoryType = models.CharField(max_length=255, null=True, blank=True)

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
    machine = models.ForeignKey('Machine')
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
        return u"{} Licence".format(self.windowsVer)

    def __str__(self):
        return self.__unicode__()


class Role(models.Model):  # Add/change
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.__unicode__()
