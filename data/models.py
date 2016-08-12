from django.db import models

from djmoney.models.fields import MoneyField

class Machine(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    notes = models.TextField()
    cType = models.ForeignKey('CType')
    manufacturer = models.ForeignKey('Manufacturer')
    compModel = models.ForeignKey('CompModel')
    ram = models.ForeignKey('RAM')
    cpu = models.ManyToManyField('CPU')
    hdd = models.ManyToManyField('HDD')
    gpu = models.ManyToManyField('GPU')
    role = models.ManyToManyField('Roles')
    network = models.ManyToManyField('Network')
    fund = models.ForeignKey('CategoricalFund')
    po = models.ForeignKey('PO')
    purchase = models.ForeignKey('Purchase')
    campus = models.ForeignKey('Campus')
    building = models.ForeignKey('Building')
    def __unicode__(self):
        return self.name
    def __str__(self):
        return self.__unicode__()

class CType(models.Model):
    DESKTOP = 'DESKTOP'
    LAPTOP = 'LAPTOP'
    SERVER = 'SERVER'
    MACHINE_TYPES = (
        (DESKTOP, 'Desktop'),
        (LAPTOP, 'Laptop'),
        (SERVER, 'Server'),
    )
    compType = models.CharField(
        max_length=6,
        choices=MACHINE_TYPES,
    )
    def __unicode__(self):
        return self.compType
    def __str__(self):
        return self.__unicode__()

class Manufacturer(models.Model):
    name = models.CharField(max_length=255)
    def __unicode__(self):
        return self.name
    def __str__(self):
        return self.__unicode__()

class CompModel(models.Model):
    name = models.CharField(max_length=255)
    def __unicode__(self):
        return self.name
    def __str__(self):
        return self.__unicode__()

class RAM(models.Model):
    size = models.PositiveSmallIntegerField()
    numberOfSticks = models.PositiveSmallIntegerField()
    def __unicode__(self):
        return u"{} GB, {} Number Of Sticks".format(self.size, self.numberOfSticks)
    def __str__(self):
        return self.__unicode__()

class CPU(models.Model):
    model = models.CharField(max_length=255)
    cores = models.PositiveSmallIntegerField()
    def __unicode__(self):
        return u"{}, {} Cores".format(self.model, self.cores)
    def __str__(self):
        return self.__unicode__()

class HDD(models.Model):
    size = models.PositiveSmallIntegerField()
    free = models.PositiveSmallIntegerField()
    def __unicode__(self):
        return u"{} GB, {} GB Free".format(self.size, self.free)
    def __str__(self):
        return self.__unicode__()

class GPU(models.Model):
    name = models.CharField(max_length=255)
    def __unicode__(self):
        return self.name
    def __str__(self):
        return self.__unicode__()

class Roles(models.Model):
    name = models.CharField(max_length=255)
    def __unicode__(self):
        return self.name
    def __str__(self):
        return self.__unicode__()

class Network(models.Model):
    name = models.CharField(max_length=255)
    mac = models.CharField(max_length=255)
    def __unicode__(self):
        return u"{}, {} Mac Address".format(self.name, self.mac)
    def __str__(self):
        return self.__unicode__()

class CategoricalFund(models.Model):
    name = models.CharField(max_length=255)
    def __unicode__(self):
        return self.name
    def __str__(self):
        return self.__unicode__()

class PO(models.Model):
    number = models.PositiveSmallIntegerField()
    def __unicode__(self):
        return self.number
    def __str__(self):
        return self.__unicode__()

class Purchase(models.Model):
    invoiceNum = models.CharField(max_length=255)
    price = MoneyField(max_digits=7, decimal_places=2, default_currency='USD')
    purchaseDate = models.DateField()
    warrantyExpDate = models.DateField()
    def __unicode__(self):
        return u"{} Invoice Number, {} Dollars, {} Purchase Date, {} Expiration Date".format(self.invoiceNum, self.price, self.purchaseDate, self.warrantyExpDate)
    def __str__(self):
        return self.__unicode__()

class Campus(models.Model):
    name = models.CharField(max_length=255)
    def __unicode__(self):
        return self.name
    def __str__(self):
        return self.__unicode__()

class Building(models.Model):
    name = models.CharField(max_length=255)
    def __unicode__(self):
        return self.name
    def __str__(self):
        return self.__unicode__()

# https://github.com/django-money/django-money
# https://docs.djangoproject.com/en/1.10/ref/models/fields/#integerfield