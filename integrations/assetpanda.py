import toml
import requests
import os.path
import json
from collections import namedtuple

# Fair warning to all, this is HIGHLY configured JUST to match my usecase. I'll likely (if I decide that I want to) go ahead and change this later, but that may be difficult being given these restraints

# stuff to run always here such as class/def
def main():
    pass

## Get Token for Auth
def getToken(config):
    # To be candid, I really have to check and find out what these items do in the API
    try:
        device = config['credentials']['assetpanda']['device']
        app_version = config['credentials']['assetpanda']['app_version']
    except KeyError:
        device = "Desktop"
        app_version = "2"

    # Grab token from a POST (as per API). Ensures request went through and did not time out
    try:
        token = requests.post('https://login.assetpanda.com:443/v2/session/token', data = {
            'client_id': config['credentials']['assetpanda']['client_id'],
            'client_secret': config['credentials']['assetpanda']['client_secret'],
            'email': config['credentials']['assetpanda']['email'],
            'password': config['credentials']['assetpanda']['password'],
            'device': device,
            'app_version': app_version
        })
    except requests.exceptions.ConnectTimeout as timeout:
        print(timeout)
        print("It seems like you've hit a timeout with the server")
        raise SystemExit
    except requests.exceptions.ConnectionError as connectErr:
        print(connectErr)
        print("We had a hard time trying to connect to the server")
        raise SystemExit

    # Makes sure there was no error connecting before going forward
    try:
        token.raise_for_status() # Raises an error if 4xx or 5xx error code. Goes through if 200
    except requests.exceptions.HTTPError as error:
        print("There was an error recieving the authorization token:")
        print(error)
        # Add more from http://docs.python-requests.org/en/latest/user/quickstart/#errors-and-exceptions
        raise SystemExit

    # Takes token recieved and gives token that's needed
    key = token.json()['token_type'].title() + " " + token.json()['access_token']
    auth = {'Authorization':key}
    return auth

def getMachineAssetID(auth, mac, entitydict, fieldsdict):
    body = {
        "field_filters": {
            fieldsdict['MAC Address']: mac
        }
    }
    cloudAsset = requests.post('https://login.assetpanda.com:443/v2/entities/' + entitydict['Assets'] + '/search_objects', headers=auth, json=body)
    return cloudAsset.json()['objects'][0][fieldsdict['Asset ID']]

## Generates dictionary with IDs matching names of entities. IE:
# Assets
def turnIDsIntoNames(auth): # This will likely be expanded to getting the IDs of all entities and then renamed
    dictionaries = {}
    entitiesjson = requests.get('https://login.assetpanda.com:443/v2/entities', headers=auth).json()
    entitydict = {}
    for entity in entitiesjson:
        entitydict[entity['name']] = entity['id']
        if (entity['name'] == "Assets"):
            fieldsdict = {}
            for field in entity['fields']:
                fieldsdict[field['name']] = field['key']
    dictcollection = namedtuple('dictcollection', ['entitydict', 'fieldsdict'])
    dictionaries = dictcollection(entitydict, fieldsdict)
    return dictionaries

def getNewAssetID(auth, entitydict, fieldsdict):
    array = requests.get('https://login.assetpanda.com:443/v2/entities/' + entitydict['Assets'] + '/objects?fields=' + fieldsdict['Asset ID'], headers=auth).json()
    try:
        return max(map(lambda object: int(object[fieldsdict['Asset ID']]), array['objects']))
    except IndexError: # If entity does not yet have an object in it
        return 0

def makeAsset(auth, info):
    dictionaries = turnIDsIntoNames(auth)
    fieldsdict = dictionaries.fieldsdict
    entitydict = dictionaries.entitydict
    body = {
        fieldsdict['Asset ID']: getNewAssetID(auth, entitydict, fieldsdict) + 1,
        fieldsdict['Name']: info.name,
        fieldsdict['RAM Size']: info.ramsize,
        fieldsdict['Network Card Model']: info.netmodel,
        fieldsdict['RAM Sticks']: info.ramsticks,
        fieldsdict['Model']: info.model,
        fieldsdict['CPU Cores']: info.cpucores,
        fieldsdict['MAC Address']: info.mac,
        fieldsdict['Server Roles']: info.roles,
        fieldsdict['CPU Model']: info.cpumodel,
        fieldsdict['Manufacturer']: info.manufacturer,
        fieldsdict['HDD Size ']: info.hddsize,
        fieldsdict['Video Card Model']: info.gpus,
        fieldsdict['Asset Category']: "Technology",
        fieldsdict['HDD Free']: info.hddfree,
        fieldsdict['Asset Sub-Category']: info.comptype
    }
    response = requests.post('https://login.assetpanda.com:443/v2/entities/' + entitydict['Assets'] + '/objects', headers=auth, json=body)
    try:
        if response.json()['code'] == 2: # From what I can tell, code 2 is an error code for something not being unique. This requires you to set up the database in such a way that things need to be unique.
            print("You already have this asset in AssetPanda")
            AssetID = getMachineAssetID(auth, info.mac, entitydict, fieldsdict)
            update = requests.patch('https://login.assetpanda.com:443/v2/entity_objects/' + AssetID, headers=auth, json=body)
            print("Asset updated in AssetPanda")
        else:
            print("Asset created in AssetPanda")
    except KeyError:
        pass
    return body[fieldsdict['Asset ID']]

# stuff only to run when not called via 'import' here
if __name__ == "__main__":
    main()
    with open(os.path.join(os.path.dirname(__file__), os.pardir, 'conf.toml')) as conffile:
        config = toml.loads(conffile.read())
    auth = getToken(config)
    
    namedfields = namedtuple('namedfields', ['ramsize', 'netmodel', 'ramsticks', 'model', 'cpucores', 'mac', 'roles', 'name', 'cpumodel', 'manufacturer', 'hddsize', 'gpus', 'hddfree', 'comptype'])
    fields = namedfields(10, "HealthNet", 9, "Onemoretime", 8, "4A:B4:LF:231:92", "This is a thing that the server does \n no way, this is also a thing the server does \n wat wat \n all up in da club", "Joe202 Mac", "Intel Lumia One", "Dontstopthedancing CO", 300, "That one thing", 200, "Laptop")
    makeAsset(auth, fields)
