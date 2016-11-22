Byte2GB = 1024 * 1024 * 1024

def WMIInfo(c, silentlyFail = False, skipUpdate = False):
    """Given wmi object c, find information and store it in the database"""

    # Grab list of network devices. Tested to see if MAC in DB
    netdevices = list(filter(
        lambda net: netDeviceTest(net),
        c.Win32_NetworkAdapter()
    ))

    if not netdevices:
        if silentlyFail:
            return
        else:
            raise LookupError(c.Win32_ComputerSystem()[-1].Name + " does not have any network devices. Please advice")

    for macaddr in netdevices:
        try:
            machine = models.Machine.objects.get(network__mac=macaddr.MACAddress)
        except ObjectDoesNotExist:
            machine = models.Machine()
        except MultipleObjectsReturned:
            if silentlyFail:
                print("You have a duplicate machine in your database")
                return
            else:
                raise MultipleObjectsReturned("You have a duplicate machine in your database!")
        else:
            break
    if machine.name:
        if skipUpdate:
            raise AlreadyInDB(machine.name, "is already in your database. Skipping")
        else:
            print(machine.name + " will be updated in the local database")
    else:
        print(c.Win32_ComputerSystem()[-1].Name + " will be created in the local database")

    machine.name = c.Win32_ComputerSystem()[-1].Name
    machine.manufacturer = c.Win32_ComputerSystem()[-1].Manufacturer.strip()
    machine.compModel = c.Win32_ComputerSystem()[-1].Model.strip()
    machine.cpu = models.CPU.objects.get_or_create(name = c.Win32_Processor()[0].Name.strip(), cores = c.Win32_ComputerSystem()[-1].NumberOfLogicalProcessors, count = len(c.Win32_Processor()))[0]
    machine.ram = models.RAM.objects.get_or_create(sticks = c.win32_PhysicalMemoryArray()[-1].MemoryDevices, size = round(int(c.Win32_ComputerSystem()[-1].TotalPhysicalMemory) / Byte2GB))[0]
    try:
        machine.save()
    except IntegrityError as err:
        if silentlyFail:
            print(machine.name + " failed to import.")
            print(err)
            return
        else:
            raise IntegrityError(err)

    machine.hdds = list(map(
        lambda hdd: models.HDD.objects.get_or_create(
            name = hdd.DeviceID,
            size = round(int(hdd.Size) / Byte2GB),
            free = round(int(hdd.FreeSpace) / Byte2GB)
        )[0],
        filter(
            lambda hdd: hdd.DriveType == 3,
            c.Win32_LogicalDisk()
        )
    ))

    if not c.Win32_VideoController():
        machine.gpus = [models.GPU.objects.get_or_create(name = 'Unknown')[0]]
    else:
        machine.gpus = list(map(
            lambda gpu: models.GPU.objects.get_or_create(
                name = gpu.Name.strip()
            )[0],
            c.Win32_VideoController()
        ))

    machine.os = c.Win32_OperatingSystem()[-1].Caption.strip()

    # Get roles and computer type
    try:
        machine.roles = list(map(
            lambda server: models.Role.objects.get_or_create(name = server.Name.strip())[0],
            c.Win32_ServerFeature()
        ))
    except:
        try:
            if c.Win32_Battery()[-1].BatteryStatus > 0:
                machine.compType = models.Machine.LAPTOP
        except IndexError:
            pass  # The default for compType is already desktop
    else:
        machine.compType = models.Machine.SERVER

    # Push network devices to machine finally
    machine.network = list(map(
        lambda net: models.Network.objects.get_or_create(
            name = net.Name.strip(),
            mac = net.MACAddress
        )[0],
        netdevices
    ))

    ## Save machine
    machine.save()
    return machine