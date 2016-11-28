import nmap
import wmi

local = wmi.WMI()


def finishIP(ip, ipRange):
    """Given string ip, append input range where blank"""
    """EG: finishIP('192.168.', '0') => '192.168.0.0'"""
    if ip[-1] == '.':
        ip = ip[:-1]
    n = ip.count('.')
    if n < 3:
        for _ in ipRange(n, 2):  # Range goes from 0-2, there are three dots in IPv4 addr.
            ip += "range"
        ip += "range"
    return ip


def getComputers(search):
    """Given string search: Return list of hosts on network"""
    nm = nmap.PortScanner()
    nm.scan(hosts=search, arguments='-sS -p 22 -n -T5')  # Remove -n to get DNS NetBIOS results
    computers = nm.all_hosts()  # Gives me an host of hosts
    return computers


def netDeviceTest(net):
    """Given Win32_NetworkAdapter object, returns if object is valid"""
    return net.MACAddress is not None and net.PhysicalAdapter and net.Manufacturer != "Microsoft" and not \
        net.PNPDeviceID.startswith("USB\\") and not net.PNPDeviceID.startswith("ROOT\\")


def getDeviceNetwork(c=local):  # Should this be moved to WMIHandler.py? It deals with WMI...
    """Given WMI object c, returns IPaddress and subnetMask"""
    validNetworkIDs = list(map(
        lambda adapter: adapter.Index,
        filter(
            lambda net: net.NetEnabled is True and netDeviceTest(net),
            c.Win32_NetworkAdapter()
        )
    ))
    netDevices = []
    for netAdapter in [netAdapter for netAdapter in c.Win32_NetworkAdapterConfiguration() if
                       (netAdapter.Index in validNetworkIDs)]:
        netDevices.append(netAdapter)
    if len(netDevices) > 1:
        i = 1
        print("There are more than one network devices currently active")
        print("Please select a device from the list given:")
        for possibleNet in netDevices:
            print(str(i) + ") " + possibleNet.Description)
            i += 1
        print("")
        while True:
            try:
                netSelection = int(input('Input: '))
                netDevices = [netDevices[netSelection - 1]]
            except ValueError:
                print("Not a number")
            except IndexError:
                print("Out of range number, try again")
            else:
                break
    return netDevices[0].IPAddress[0], netDevices[0].IPSubnet[0]
