# This file will handle the plugin system and serve as a middle-man psuedo-library for all calls to said plugins
import collections
import os
from integrations import assetpanda  # Replace with plugin!

# Database info
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

# DB models and exceptions
from data import models


def getAuth(credentials):
    """Given dictionary credentials, get the auth token from plugin"""
    return assetpanda.getToken(credentials)  # Replace with plugin!


def makeAllAssets(auth):
    """Takes all Machine objects without cloudIDs and makes the asset remotely. Aught to return a list of IDs"""
    for machine in models.Machine.objects.all().filter(cloudID=None):
        print(machine.name + " will now be added to the asset tracker")
        assetReply = assetpanda.makeAsset(machine, auth)  # Replace with plugin!
        if assetReply:
            machine.cloudID = assetReply
            machine.save()


def updateCloudID(auth, machines=models.Machine.objects.all()):
    """Given list or single Machine object, update cloudID"""
    if isinstance(machines, collections.Iterable):
        for machine in machines:  # This needs to modified as it explicitly calls for models.
            machine.cloudID = assetpanda.getMachineAssetID(machine.network.first().mac, auth)  # Replace with plugin!
            machine.save()
    else:
        machines.cloudID = assetpanda.getMachineAssetID(machines.network.first().mac, auth)  # Replace with plugin!
        machines.save()
