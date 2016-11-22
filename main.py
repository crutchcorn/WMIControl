"""WMIControl - For those hard to reach servers. UoNC eat your heart out

Usage:
  WMIControl scan
  WMIControl scan <nmapIP>
  WMIControl scan <start> <end>
  WMIControl scan (-s | --subnet)
  WMIControl scan updatedb
  WMIControl settings (skip | silent)

Options:
  -h --help                  Show this screen
  -v --version               Show version
  scan                       Start a local or remote scan        IE: When empty, local
  <nmapIP>                   A valid nmap IP query to call       EG: 192.168.1.1/24
  <start> <end>              Scan a range of IP addresses        EG: 192.168.1.0 192.168.1.255
  -s --subnet                Scan through the entire subnet
  updatedb                   Update the local DB with cloud IDs

"""

# Core imports
import sys
import os

# Custom Imports
from docopt import docopt
import wmi
import nmap
import toml
from integrations import assetpanda #! Replace with plugin
from netaddr import IPNetwork

# Local imports
from networkMngr import finishIP, getComputers, netDeviceTest, getDeviceNetwork
from wmihandler import WMIInfo
from pluginHelper import makeAllAssets

# Database info
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
from django.core.wsgi import get_wsgi_application
from django.conf import settings
application = get_wsgi_application()

# DB models and exceptions
from data import models
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import IntegrityError

# Global definitions
class AlreadyInDB(Exception):
    """Custom error to readably find duplicate items."""
    pass

# Load config file
with open("conf.toml") as conffile:
    config = toml.loads(conffile.read())

def main():
    # Grab CLI Arguments
    arguments = docopt(__doc__, version='WMIControl 0.1')

    # Handle CLI Arguments
    if arguments['scan']:
        local = wmi.WMI()
        if arguments['<nmapIP>'] or arguments['<start>'] or arguments['--subnet']:
            if arguments['<start>']:
                start = tuple(part for part in finishIP(arguments['<start>'], "0").split('.'))
                end = tuple(part for part in finishIP(arguments['<end>'], "255").split('.'))
                search = ""
                for s,e in zip(start, end):
                    if (s == e):
                        search += s
                    else:
                        search += "{0}-{1}".format(s, e) 
                    search += '.'
                search = search[:-1]
            elif arguments['<nmapIP>']:
                search = finishIP(arguments['<nmapIP>'], "0-255")
            elif arguments['--subnet']:
                ip, subnet = getDeviceNetwork(local)
                search = str(IPNetwork(ip+"/"+subnet).cidr)
            for ip in getComputers(search):
                for i in range(len(config['credentials']['wmi']['users'])):
                    print("Trying to connect to", ip, "with user '" + config['credentials']['wmi']['users'][i] + "'")
                    try:
                        c = wmi.WMI(str(ip), user=config['credentials']['wmi']['users'][i], password=config['credentials']['wmi']['passwords'][i])
                        WMIInfo(c, config['settings']['silentlyFail'], config['settings']['skipUpdate'])
                    except wmi.x_wmi as e:
                        if(e.com_error.excepinfo[2] == 'The RPC server is unavailable. '):  # This is unfornutately the way this must be done. There is no error codes in wmi library AFAIK
                            print("Computer does not have WMI enabled")
                            break
                        else:
                            print(e.com_error.excepinfo[2])
                    except AlreadyInDB as inDBErr:
                        print(inDBErr)
                        break
                    except IndexError:
                        raise IndexError("Your configuration file is configured incorrectly")
                    else:
                        break
        else:
            WMIInfo(local, config['settings']['silentlyFail'], config['settings']['skipUpdate'])
        # makeAllAssets()  # Uncomment me
    elif arguments['updatedb']:
        for machine in models.Machine.objects.all():
            machine.cloudID = assetpanda.getMachineAssetID(machine.network.first().mac, auth)  # Replace with plugin
            machine.save()
    elif arguments['settings']:
        if arguments['skip']:
            config['settings']['skipUpdate'] = not config['settings']['skipUpdate']
            print("Skipping switch has been toggled.")
            print("Value is now: " + str(config['settings']['skipUpdate']))
        elif arguments['silent']:
            config['settings']['silentlyFail'] = not config['settings']['silentlyFail']
            print("Silence switch has been toggled.")
            print("Value is now: " + str(config['settings']['silentlyFail']))
        with open("conf.toml", "w") as updateConfig:
            updateConfig.write(toml.dumps(config))

if __name__ == "__main__":
    main()