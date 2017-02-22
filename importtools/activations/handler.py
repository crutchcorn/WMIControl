# DB models and exceptions
from lib.setSettings import djangopath
djangopath(up=2, settings='settings')
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from data import models
from uuid import uuid4
import csv

# Database info
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError

def hasRelatedMachine(self):
    return hasattr(self, 'machine')


def findOrCreateMachine(macAddr, activateObj=None):
    """Given a mac address and optional activation object, finds associated machine or creates a boilerplate for it"""
    try:
        computer = models.Machine.objects.get(network__mac=macAddr)
    except models.Machine.DoesNotExist:
        computer = createBoilerplateMachine(macAddr, activateObj)
    return computer


def createBoilerplateMachine(macAddr, activateObj=None):
    """Given a mac address and optional activation object, creates and returns a new boilerplate machine with a UUID4
    name. This shouldn't conflict with other automatically created machines as the UUID is too long a name for
    netbios.
    """
    computer = models.Machine.objects.create(name=str(uuid4()), activation=activateObj)
    models.Network.objects.create(machine=computer, mac=macAddr)
    return computer


def xNone(n):
    """Takes n and returns None if n is an empty string"""
    return None if n is '' else n


def importCSV(csvFile):
    with open(csvFile) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                activation = models.Activation.objects.create(COAID=xNone(row['COA']),
                                                              productKey=row['ProductKey'],
                                                              securityCode=xNone(row['SecurityCode']),
                                                              windowsVer=row['WindowsVer'])
            except IntegrityError:
                raise IntegrityError("The following Activation object had problems being created; COA: "
                                     + row['COA'], "ProductKey: " + row['ProductKey'])
            # If MAC address was given, assign the activation key to the machine
            if row['MAC']:
                findOrCreateMachine(row['MAC'], activation)


def retireCSV(csvFile, silentlyFail=False):
    activationObjects = models.Activation.objects.all()
    with open(csvFile) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['MAC']:
                try:
                    machine = models.Machine.objects.get(mac=row['MAC'])
                except models.Machine.DoesNotExist:
                    raise ObjectDoesNotExist("No machine with the mac address" + row['MAC'] + "could be found.")
                else:
                    machine.activation = None
                    machine.save()
            else:
                activationObject = activationObjects
                # For each key in row. EG: {"MAC":"", "COA":"", "ProductKey":""}
                # Done this way to avoid using some messy if combo here. Fairly efficient as QuerySets are lazy
                # http://stackoverflow.com/questions/7006862/query-when-parameter-is-none-django
                for key, value in row:
                    if key == 'COA' and value:
                        activationObject = activationObject.filter(COAID=row['COA'])
                    elif key == 'ProductKey' and value:
                        activationObject = activationObject.filter(COAID=row['ProductKey'])
                    else:
                        raise KeyError(
                            "The data in this line of the CSV is blank or invalid. Please check the data "
                            "and try again")
                if activationObject:
                    activationObject.delete()
                else:
                    errString = "No product key could be found matching your requirements; COA: " + \
                                row['COA'], "ProductKey: " + row['ProductKey']
                    if silentlyFail:
                        print(errString)
                    else:
                        raise ObjectDoesNotExist(errString)


def searchActivation(toFind, arg):
    try:
        if toFind is 'mac':
            results = models.Machine.objects.get(network__mac=arg).activation
        elif toFind is 'coa':
            results = models.Activation.objects.get(COAID=arg)
        elif toFind is 'prodkey':
            results = models.Activation.objects.get(productKey=arg)
        else:
            print("The command line arguments supplied are incorrect. Please try again")
            print("")
            raise SyntaxError
    except ObjectDoesNotExist:
        print("No object matches the query requested")
    else:
        print("The object matching your query requested is as follows:")
        if hasRelatedMachine(results):
            print("MAC: " + str(results.machine.network_set.first().mac))
        print("COA: " + results.COAID)
        print("WindowsVer: " + results.windowsVer)
        print("ProductKey: " + results.productKey)
        print("SecurityCode: " + results.securityCode)
