import wmi
import json
from copy import deepcopy
c = wmi.WMI()
def netDeviceTest(net):
    """Given Win32_NetworkAdapter object, returns if object is valid"""
    return net.MACAddress is not None and net.PhysicalAdapter and net.Manufacturer != "Microsoft" and not \
        net.PNPDeviceID.startswith("USB\\") and not net.PNPDeviceID.startswith("ROOT\\")



with open('flags.json') as flagsJSON:
    flags = json.load(flagsJSON)

newNetworks = {
    "netObjs": [],
    "flags": {
        "netDevices": [],
        "selectedNet": ""
    }
}

flagCheck = [not not flags[k] for k in ['netDevices', 'selectedNet'] if k in flags]
if all([all(flagCheck), len(flagCheck) == 2]):  # If both are in the `flags` dict
    newNetworks['flags'] = deepcopy(flags)
else:  # Otherwise, get rid of data
    flags.update(newNetworks['flags'])
    newNetworks['flags'] = deepcopy(flags)

validNetworkIDs = list(map(
    lambda adapter: adapter.Index,
    filter(
        lambda net: netDeviceTest(net),
        c.Win32_NetworkAdapter()
    )
))

for netAdapter in [netAdapter for netAdapter in c.Win32_NetworkAdapterConfiguration() if
                   (netAdapter.Index in validNetworkIDs)]:
    newNetworks['netObjs'].append(netAdapter)
    newNetworks['flags']['netDevices'].append(netAdapter.MACAddress)

newFlags = newNetworks['flags']['netDevices']
print(flags['netDevices'])
print(newFlags)
same = set(flags['netDevices']) != set(newFlags)
print(same)
if (len(newFlags) > 1) and same:
    # `or` force reset network flag was not set
    i = 1
    print("There are more than one network devices currently active")
    print("Please select a device from the list given:")
    for possibleNet in newNetworks['netObjs']:
        print(str(i) + ") " + possibleNet.Description)
        i += 1
    print("")
    while True:
        try:
            netSelection = int(input('Input: '))
            newNetworks['flags']['selectedNet'] = newFlags[netSelection - 1]
        except ValueError:
            print("Not a number, try again")
        except IndexError:
            print("Out of range number, try again")
        else:
            break

print(newNetworks['flags'])
with open('flags.json', 'w') as f:
    json.dump(newNetworks['flags'], f)
