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
    MACHINE_TYPES = (
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
    cpu = models.ManyToManyField('CPU', blank=True)  # Many to many, as CPUs are not unique.
    ram = models.ManyToManyField('RAM', blank=True)  # Many to many, as RAM is not unique.
    # Should be one to many in the future, HDDs are not unique. However, free space is fairly unique.
    # This will likely be solved by making free space some type of calculation rather than a field in the DB soon
    hdds = models.ManyToManyField('HDD', blank=True)
    gpus = models.ManyToManyField('GPU', blank=True)
    os = models.CharField(max_length=255, blank=True)
    activation = models.OneToOneField('Activation', null=True, blank=True) # Licences have parent-child relationship
    roles = models.ManyToManyField('Role', blank=True)  # Roles are not unique
    cloudID = models.PositiveSmallIntegerField(null=True, blank=True, unique=True)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.__unicode__()


class CPU(models.Model):
    name = models.CharField(max_length=255)
    count = models.PositiveSmallIntegerField()
    cores = models.PositiveSmallIntegerField()

    def __unicode__(self):
        return u"{}, {} Cores".format(self.name, self.cores)

    def __str__(self):
        return self.__unicode__()


class RAM(models.Model):
    size = models.PositiveSmallIntegerField()
    sticks = models.PositiveSmallIntegerField(null=True, blank=True)

    def __unicode__(self):
        return u"{} GB, {} Number Of Sticks".format(self.size, self.sticks)

    def __str__(self):
        return self.__unicode__()


class HDD(models.Model):
    name = models.CharField(max_length=255, blank=True)
    size = models.PositiveSmallIntegerField()
    free = models.PositiveSmallIntegerField(null=True, blank=True)

    def __unicode__(self):
        return u"{} Mount, {} GB, {} GB Free".format(self.name, self.size, self.free)

    def __str__(self):
        return self.__unicode__()


class GPU(models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.__unicode__()


class Network(models.Model):
    machine = models.ForeignKey('Machine')  # One to many, network cards ARE unique and can be moved (MAC addresses)
    name = models.CharField(max_length=255, blank=True, null=True)
    mac = MACAddressField(unique=True)

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


class Role(models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.__unicode__()

# https://github.com/django-money/django-money
# https://docs.djangoproject.com/en/1.10/ref/models/fields/#integerfield
# http://stackoverflow.com/questions/3113885/difference-between-one-to-many-many-to-one-and-many-to-many
