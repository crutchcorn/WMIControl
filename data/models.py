from django.db import models

from djmoney.models.fields import MoneyField

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
    name = models.CharField(max_length=255)
    manufacturer = models.CharField(max_length=255, blank=True)
    compModel = models.CharField(max_length=255, blank=True)
    cpu = models.ForeignKey('CPU', null=True, blank=True)
    ram = models.ForeignKey('RAM', null=True, blank=True)
    hdds = models.ManyToManyField('HDD', null=True, blank=True)
    gpus = models.ManyToManyField('GPU', null=True, blank=True)
    network = models.ManyToManyField('Network')
    os = models.CharField(max_length=255, blank=True)
    roles = models.ManyToManyField('Role', null=True, blank=True)
    cloudID = models.PositiveSmallIntegerField(null=True, blank=True)
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
    name = models.CharField(max_length=255, blank=True)
    mac = models.CharField(max_length=255)
    def __unicode__(self):
        return u"{}, {} Mac Address".format(self.name, self.mac)
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