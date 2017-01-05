import nmap
import wmi
import socket
from struct import pack
from netaddr import IPNetwork


local = wmi.WMI()


def netDeviceTest(net):
    """Given Win32_NetworkAdapter object, returns if object is valid"""
    return net.MACAddress is not None and net.PhysicalAdapter and net.Manufacturer != "Microsoft" and not \
        net.PNPDeviceID.startswith("USB\\") and not net.PNPDeviceID.startswith("ROOT\\")


def getDeviceNetwork(c=None):
    """Given WMI object c, returns IPaddress, subnetMask, and cidr

    While inconvinient, I am having cidrNet as the third item as you can simply call it in functions

    This function has a bug that when imported, it will run. Though I know the root cause I don't know the solution
    The root cause is that Python precompiles default calls"""

    if not c:
        c = local

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
                print("Not a number, try again")
            except IndexError:
                print("Out of range number, try again")
            else:
                break
    ip = netDevices[0].IPAddress[0]
    subnet = netDevices[0].IPSubnet[0]
    cidr = str(IPNetwork(ip + "/" + subnet).cidr)
    return ip, subnet, cidr


def finishIP(ip, ipRange):
    """Given string ip, append input range where blank
    >>> finishIP('192.168.', '0')
    '192.168.0.0'"""
    if ip[-1] is '.':
        ip = ip[:-1]
    n = ip.count('.')
    if n < 3:
        for _ in ipRange(n, 2):  # Range goes from 0-2, there are three dots in IPv4 address.
            ip += "range"
        ip += "range"
    return ip


def getComputers(search=None, args=None):
    """Given string search and string args: Return list of hosts on network
    'args' being nmap arguments to be passed to nmap for optimized searching on networks

    'search' defaults to current network subnet
    'args' defaults to '-sS -p 22 -n -T5'"""
    if not search:
        _, _, search = getDeviceNetwork()
    if not args:
        args = '-sS -p 22 -n -T5'
    nm = nmap.PortScanner()
    scanInfo = nm.scan(hosts=search, arguments=args)  # Remove -n to get DNS NetBIOS results
    IPs = nm.all_hosts()  # Gives me an host of hosts
    return IPs, scanInfo


def listNetDevices():
    """Returns a list of all device's hostnames on the network"""
    _, a = getComputers(getDeviceNetwork()[2], '-sS -p 22')
    ips = [info['hostnames'][0]['name'] for _, info in a['scan'].items()]
    return list(filter(None, ips))


def findBroadcast(ip=None, subnet=None):
    """Given string ip, subnet: Find WoL broadcast IP.
    Leave blank to use getDeviceNetwork as ip and subnet retreval"""
    if not ip:
        ip, subnet, _ = getDeviceNetwork()
    return ".".join([str((int(ip.split('.')[i]) | int(subnet.split('.')[i]) ^ 255)) for i in range(0, 4)])


def sendWoL(mac, broadcast=findBroadcast()):
    """Given string mac and broadcast: Turn on computer using WoL
    This was taken from http://code.activestate.com/recipes/358449-wake-on-lan/. Thanks, Fadly!"""
    # Checks if mac address has delimiters
    if len(mac) == 12:
        pass
    elif len(mac) == 12 + 5:
        seperator = mac[2]
        mac = mac.replace(seperator, '')
    else:
        raise ValueError('Incorrect MAC address format')

    # Pad the synchronization stream.
    data = ''.join(['FFFFFFFFFFFF', mac * 20])
    send_data = b''

    # Split up the hex values and pack.
    for i in range(0, len(data), 2):
        send_data = b''.join([send_data, pack('B', int(data[i: i + 2], 16))])

    # Broadcast it to the LAN.
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(send_data, (broadcast, 7))
