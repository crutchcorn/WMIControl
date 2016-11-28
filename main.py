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

# Custom Imports
from docopt import docopt
from netaddr import IPNetwork
import toml

# Local imports
from networkMngr import finishIP, getDeviceNetwork
from wmihandler import WMIInfo, getWMIObjs
from pluginHelper import makeAllAssets, updateCloudID, getAuth
from exceptions import AlreadyInDB

# Load config file
with open("conf.toml") as conffile:
    config = toml.loads(conffile.read())


def main():
    # Get auth key from asset tracker
    # auth = getAuth(config['credentials']['assetpanda'])  # Replace with plugin!

    # Grab CLI Arguments
    arguments = docopt(__doc__, version='WMIControl 0.1')

    # Handle CLI Arguments
    if arguments['scan']:
        search = ""
        if arguments['<nmapIP>'] or arguments['<start>'] or arguments['--subnet']:
            if arguments['<start>']:
                start = tuple(part for part in finishIP(arguments['<start>'], "0").split('.'))
                end = tuple(part for part in finishIP(arguments['<end>'], "255").split('.'))
                for s, e in zip(start, end):
                    if s == e:
                        search += s
                    else:
                        search += "{0}-{1}".format(s, e)
                    search += '.'
                search = search[:-1]
            elif arguments['<nmapIP>']:
                search = finishIP(arguments['<nmapIP>'], "0-255")
            elif arguments['--subnet']:
                ip, subnet = getDeviceNetwork()
                search = str(IPNetwork(ip + "/" + subnet).cidr)
            for comp in getWMIObjs(search, config['credentials']['wmi']['users']):
                try:
                    WMIInfo(config['settings']['silentlyFail'], config['settings']['skipUpdate'], comp)
                except AlreadyInDB as inDBErr:
                    print(inDBErr)
                    break
                except IndexError:
                    raise IndexError("Your configuration file is configured incorrectly")
        else:
            try:
                WMIInfo(config['settings']['silentlyFail'], config['settings']['skipUpdate'])
            except AlreadyInDB as inDBErr:
                print(inDBErr)
            except IndexError:
                raise IndexError("Your configuration file is configured incorrectly")
        # makeAllAssets(auth)  # Uncomment me
    # elif arguments['updatedb']:
    #     updateCloudID(auth)
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
