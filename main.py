"""WMIControl - For those hard to reach servers. UoNC eat your heart out

Usage:
    WMIControl scan [<nmapIP> <args>]
    WMIControl scan (-r | --range) <start> <end>
    WMIControl scan (-s | --subnet)
    WMIControl control [<file> [<nmapIP>]]
    WMIControl settings (skip | silent)
    WMIControl shell

Options:
    -h --help           ~ Show this screen
    -v --version        ~ Show version

    scan                ~ Start a scan to import assets into DB.
        ----------------------------------------------------------------
        When no parameters passed, it scans the local machine into the DB

    <nmapIP> <args>     ~ Valid nmap IP and arguments                              EG: 192.168.1.1/24 ["-p 22 -n -T2"]
        ----------------------------------------------------------------
        If <nmapIP> ip is left incomplete, it will finish it with '0-255'.         EG: 192.168.1 becomes 192.168.1.0-255
        <args> must be passed in by a list containing a string

    <start> <end>       ~ Scan a range of IP addresses                             EG: 192.168.1.0 192.168.1.255
        ----------------------------------------------------------------
        If <start>  ip is left incomplete, it will finish it with 0s.              EG: 192.168.1 becomes 192.168.1.0
        If <end>    ip is left incomplete, it will finish it with 255s.            EG: 192.168.1 becomes 192.168.1.255

    -s --subnet         ~ Scan through the entire subnet currently being used
        ----------------------------------------------------------------
        If machine has more than one network device in use, it will prompt you which to use

    control             ~ Take control of assets already scanned into local DB.
        ----------------------------------------------------------------
        When no parameters passed, it starts a command line type session to interactively control assets.

    <file>              ~ Run a file on assets. Accepts range <nmapIP>             EG: file.txt 192.168.1.100
        ----------------------------------------------------------------
        If <nmapIP> is left blank, <file> will run on every asset on the subnet
        If <nmapIP> ip is left incomplete, it will finish it with '0-255'.         EG: 192.168.1 becomes 192.168.1.0-255
        (More ways to select assets to run will come soon)

    settings            ~ Modify settings for WMIControl
        ----------------------------------------------------------------
        skip            ~ A toggle to skip updating assets that have already been added to your database.
        silent          ~ A toggle to silence any non-max-level-crutial errors while scanning.

    shell               ~ A shell that you can drop down to to run more advanced program functions
"""

# Custom Imports
import toml
from docopt import docopt
import firstrun
firstrun.main()

from lib.excepts import AlreadyInDB
from lib.networkMngr import finishIP, getDeviceNetwork
from wmiskai.wmiControl import runFile
from wmiskai.wmiScanner import WMIInfo, getWMIObjs
from lib.skaishell import SkaiShell
from os.path import join, expanduser
# Load config file

with open(join(expanduser('~'), "conf.toml")) as conffile:
    config = toml.loads(conffile.read())


def switchSettings(value):
        config['settings'][value] = not config['settings'][value]
        print(value.title() + "switch has been toggled.")
        print("Value is now: " + str(config['settings'][value]))
        return config

silentAndSkipDefaults = (config['settings']['silentlyFail'], config['settings']['skipUpdate'])


def finishIt(startorEnd, number, arguments):
    return tuple(part for part in finishIP(arguments['<' + startorEnd + '>'], str(number)).split('.'))


def WMIObjDefaults(serch, arguments):
    return config['credentials']['wmi']['users'], serch, arguments['<args>']


def main():
    # Get auth key from asset tracker
    # auth = getAuth(config['credentials']['assetpanda'])  # Replace with plugin!

    # Grab CLI Arguments
    arguments = docopt(__doc__, version='WMIControl 0.1')
    # This will finish (see finishIP) and split up an IP address into a list


    # Handle CLI Arguments
    if arguments['scan']:
        search = ""
        if arguments['<nmapIP>'] or arguments['--range'] or arguments['--subnet']:
            if arguments['--range']:
                start = finishIt("start", 0, arguments)
                end = finishIt("end", 255, arguments)
                for s, e in zip(start, end):
                    if s is e:
                        search += s
                    else:
                        search += "{0}-{1}".format(s, e)
                    search += '.'
                search = search[:-1]
            elif arguments['<nmapIP>']:
                search = finishIP(arguments['<nmapIP>'], "0-255")
                if arguments['<args>']:
                    search = [search, arguments['<args>']]
            elif arguments['--subnet']:
                _, _, search = getDeviceNetwork()
            for comp in getWMIObjs(*WMIObjDefaults(search, arguments)):
                try:
                    WMIInfo(comp, *silentAndSkipDefaults)
                except AlreadyInDB as inDBErr:
                    print(inDBErr)
                    break
                except IndexError:
                    raise IndexError("Your configuration file is configured incorrectly")
        else:
            try:
                WMIInfo(None, *silentAndSkipDefaults)
            except AlreadyInDB as inDBErr:
                print(inDBErr)
            except IndexError:
                raise IndexError("Your configuration file is configured incorrectly")
        # makeAllAssets(auth)  # Uncomment me to have assets be created on the remote asset tracker

    # elif arguments['updatedb']:
    #     updateCloudID(auth)

    #     """
    #     Usage:
    #     WMIControl scan updatedb
    #
    #     Options:
    #     updatedb - Update the local DB assets with cloud IDs
    #
    #     """

    elif arguments['settings']:
        if arguments['skip'] or arguments['silentyFail']:
            if arguments['skip']:
                newConfig = switchSettings("skipUpdate")
            elif arguments['silent']:
                newConfig = switchSettings("silentlyFail")
            with open(join(expanduser('~'), "conf.toml"), "w") as updateConfig:
                updateConfig.write(toml.dumps(newConfig))
        else:
            pass

    elif arguments['control']:
        # Select which computers to control
        if arguments['<file>']:
            if arguments['<nmapIP>']:
                search = finishIP(arguments['<nmapIP>'], "0-255")
            else:
                _, _, search = getDeviceNetwork()

            for comp in getWMIObjs(*WMIObjDefaults(search, arguments)):
                runFile(comp, arguments['<file>'])
        else:
            # cmd.py will go here. Unfortunately cmd.py is not done (or hardly started, even)
            print("Sorry, this feature is still in development. Please use <file> to run commands")

    elif arguments['shell']:
        SkaiShell().cmdloop()

if __name__ == "__main__":
    main()
