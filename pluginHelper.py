# This file will handle the plugin system and serve as a middle-man psuedo-library for all calls to said plugins

def getAuth(config):
    return assetpanda.getToken(config) #! Replace with plugin # Uncomment me

def makeAllAssets():
    """Takes all Machine objects without cloudIDs and makes the asset remotely"""
    for machine in models.Machine.objects.all().filter(cloudID=None):
        print(machine.name + " will now be added to the asset tracker")
        assetReply = assetpanda.makeAsset(machine, auth) #! Replace with plugin
        if assetReply:
            machine.cloudID = assetReply
            machine.save()
