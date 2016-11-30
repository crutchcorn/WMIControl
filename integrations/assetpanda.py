# Fair warning to all, this is HIGHLY configured JUST to match my usecase.
# I'll likely (if I decide that I want to) go ahead and change this later, but that may be difficult.
import requests


# Get Token for Auth
def getToken(config):
    """Given dictionary config: Return auth token"""
    # To be candid, I really have to check and find out what these items do in the API
    try:
        device = config['device']
        app_version = config['app_version']
    except KeyError:
        device = "Desktop"
        app_version = "2"

    # Grab token from a POST (as per API). Ensures request went through and did not time out
    try:
        token = requests.post('https://login.assetpanda.com:443/v2/session/token', data={
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'email': config['email'],
            'password': config['password'],
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
        token.raise_for_status()  # Raises an error if 4xx or 5xx error code. Goes through if 200
    except requests.exceptions.HTTPError as error:
        print("There was an error recieving the authorization token:")
        print(error)
        # Add more from http://docs.python-requests.org/en/latest/user/quickstart/#errors-and-exceptions
        raise SystemExit

    # Takes token recieved and gives token that's needed
    key = token.json()['token_type'].title() + " " + token.json()['access_token']
    auth = {'Authorization': key}
    return auth


def getMachineAssetID(mac, auth):
    """Given a mac address and auth key, return an asset ID"""
    entitydict, fieldsdict = turnIDsIntoNames(auth)
    body = {
        "field_filters": {
            fieldsdict['MAC Address']: mac
        }
    }
    cloudAsset = requests.post(
        'https://login.assetpanda.com:443/v2/entities/' + entitydict['Assets'] + '/search_objects', headers=auth,
        json=body)
    if len(cloudAsset.json()['objects']):
        return cloudAsset.json()['objects'][0][fieldsdict['Asset ID']]
    else:
        return


# Generates dictionary with IDs matching names of entities. IE:
# Assets
def turnIDsIntoNames(auth):  # This will likely be expanded to getting the IDs of all entities and then renamed
    """Given auth key, return entitydict and fieldsdict for better readability of code"""
    entitiesjson = requests.get('https://login.assetpanda.com:443/v2/entities', headers=auth).json()
    entitydict = {}
    fieldsdict = {}
    for entity in entitiesjson:
        entitydict[entity['name']] = entity['id']
        if entity['name'] == "Assets":
            for field in entity['fields']:
                fieldsdict[field['name']] = field['key']
    return entitydict, fieldsdict


def getNewAssetID(auth):
    """Given auth key, return an asset id for a new asset"""
    entitydict, fieldsdict = turnIDsIntoNames(auth)
    array = requests.get(
        'https://login.assetpanda.com:443/v2/entities/' + entitydict['Assets'] + '/objects?fields=' + fieldsdict[
            'Asset ID'], headers=auth).json()
    try:
        return max(map(lambda obj: int(obj[fieldsdict['Asset ID']]), array['objects']))
    except IndexError:  # If entity does not yet have an object in it
        return 0


def makeAsset(machine, auth):
    """Given Machine object and auth key, create new asset. Returns ID of asset"""
    entitydict, fieldsdict = turnIDsIntoNames(auth)
    roles = machine.roles.all()
    concatenatedRoles = ""
    for role in roles:
        concatenatedRoles += str(role) + '\n'
    body = {
        fieldsdict['Asset ID']: getNewAssetID(auth) + 1,
        fieldsdict['Name']: machine.name,
        fieldsdict['RAM Size']: machine.ram.size,
        fieldsdict['Network Card Model']: machine.network_set.first().name,
        fieldsdict['RAM Sticks']: machine.ram.sticks,
        fieldsdict['Model']: machine.compModel,
        fieldsdict['CPU Cores']: machine.cpu.cores,
        fieldsdict['MAC Address']: machine.network_set.first().mac,
        fieldsdict['Server Roles']: concatenatedRoles,
        fieldsdict['CPU Model']: machine.cpu.name,
        fieldsdict['Manufacturer']: machine.manufacturer,
        fieldsdict['HDD Size ']: machine.hdds.first().size,
        fieldsdict['Video Card Model']: machine.gpus.first().name,
        fieldsdict['Asset Category']: "Technology",
        fieldsdict['HDD Free']: machine.hdds.first().free,
        fieldsdict['Asset Sub-Category']: machine.get_compType_display()
    }

    response = requests.post('https://login.assetpanda.com:443/v2/entities/31321/objects', headers=auth, json=body)
    try:
        # From what I can tell, code 2 is an error code for something not being unique.
        if response.json()['code'] == 2:
            try:
                response.json()['errors'][0][fieldsdict['MAC Address']]
            except:
                raise NameError("There is already an asset in AssetPanda called " + machine.name)
            else:
                print("You already have this asset in AssetPanda")
                AssetID = getMachineAssetID(machine.network_set.first().mac, auth)
                body[fieldsdict['Asset ID']] = AssetID
                requests.patch('https://login.assetpanda.com:443/v2/entity_objects/' + AssetID, headers=auth,
                               json=body)
                print("Asset updated in AssetPanda")
        else:
            print("Asset created in AssetPanda")
    except KeyError:
        pass
    return body[fieldsdict['Asset ID']]
