import toml
import requests
import os.path
import json

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

    # Grab token from a POST (as per API)   
    token = requests.post('https://login.assetpanda.com:443/v2/session/token', data = {
        'client_id': config['credentials']['assetpanda']['client_id'],
        'client_secret': config['credentials']['assetpanda']['client_secret'],
        'email': config['credentials']['assetpanda']['email'],
        'password': config['credentials']['assetpanda']['password'],
        'device': device,
        'app_version': app_version
    })

    # Makes sure there was no error connecting before going forward
    try:
        token.raise_for_status()
    except requests.exceptions.HTTPError:
        print("There was an error")
        return

    # Takes token recieved and gives token that's needed
    key = token.json()['token_type'].title() + " " + token.json()['access_token']
    auth = {'Authorization':key}
    return auth

# stuff only to run when not called via 'import' here
if __name__ == "__main__":
    main()
    with open(os.path.join(os.path.dirname(__file__), os.pardir, 'conf.toml')) as conffile:
        config = toml.loads(conffile.read())

    auth = getToken(config)
    w = requests.get('https://login.assetpanda.com:443/v2/entities', headers=auth)

    with open('data.json', 'w') as outfile:
        json.dump(w.json(), outfile)