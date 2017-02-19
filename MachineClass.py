# Core imports
import os

# Database info
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

# DB models and exceptions
from data import models


class Machine:
    """ To pass through items, you can consider it assigned as such
    self.processors = [{"processor": processors, "cpu_model": cpu_models}]
    self.rams = [{"ram_stick": ram_sticks, "ram_model": ram_models}]
    self.gpus = [{"gpu_card": gpu_cards, "gpu_model": gpu_models}]
    self.networks = [{"network_card": network_cards, "network_model": network_models}]
    self.physical_disks = [{"physical_disk_model": physical_disk_models, "physical_disk": physical_disks}]
    """

    def __init__(self, machine=models.Machine(), model=models.MachineModel(), processors=None, rams=None, gpus=None,
                 networks=None, physical_disks=None, logic_disks=None):
        self.machine = machine
        self.model = model
        self.processors = processors or []
        self.rams = rams or []
        self.gpus = gpus or []
        self.networks = networks or []
        self.physical_disks = physical_disks or []
        self.logic_disks = logic_disks or []

    def save(self):
        self.model.save()
        self.machine.save()
        self.save_gpus()
        self.save_networks()
        self.save_physical_disks()
        self.save_logic_disks()
        self.save_processors()
        self.save_rams()
        return self.machine

    @staticmethod
    def save_object(objectToSave, model, item):
        objectToSave[model].save()
        objectToSave[item].save()

    def createCPU(self, name, manufacturer, arch, partnum=None, family=None, upgradeMethod=None, cores=None,
                  threads=None, speed=None, serial=None, location=None):
        cpu_model, _ = models.CPUModel.objects.get_or_create(
            name=name,
            manufacturer=manufacturer,
            partnum=partnum,
            arch=arch,
            family=family,
            upgradeMethod=upgradeMethod,
            cores=cores,
            threads=threads,
            speed=speed
        )

        processor, _ = models.CPU.objects.get_or_create(
            machine=self.machine,
            model=cpu_model,
            serial=serial,
            location=location
        )

        self.processors.append({"processor": processor, "cpu_model": cpu_model})
        return processor, cpu_model

    def save_processors(self):
        for processor in self.processors:
            self.save_object(processor, "cpu_model", "processor")

    def createRAM(self, size, manufacturer=None, partnum=None, speed=None, formFactor=None, memoryType=None,
                  serial=None, location=None):
        ram_model, _ = models.RAMModel.objects.get_or_create(
            size=size,
            manufacturer=manufacturer,
            partnum=partnum,
            speed=speed,
            formFactor=formFactor,
            memoryType=memoryType
        )

        ram_stick, _ = models.RAM.objects.get_or_create(
            machine=self.machine,
            model=ram_model,
            serial=serial,
            location=location
        )
        self.rams.append({"ram_stick": ram_stick, "ram_model": ram_model})
        return ram_stick, ram_model

    def save_rams(self):
        for ram in self.rams:
            self.save_object(ram, "ram_model", "ram_stick")

    def createLAN(self, name, mac, manufacturer=None, location=None):
        network_model, _ = models.NetworkModel.objects.get_or_create(
            name=name,
            manufacturer=manufacturer
        )

        network_card, _ = models.Network.objects.get_or_create(
            machine=self.machine,
            model=network_model,
            mac=mac,
            location=location,
        )
        self.networks.append({"network_card": network_card, "network_model": network_model})
        return network_card, network_model

    def save_networks(self):
        for network in self.networks:
            self.save_object(network, "network_model", "network_card")

    def createGPU(self, name, size=None, refresh=None, arch=None, memoryType=None, location=None):
        gpu_model, _ = models.GPUModel.objects.get_or_create(
            name=name,
            size=size,
            refresh=refresh,
            arch=arch,
            memoryType=memoryType
        )

        gpu_card, _ = models.GPU.objects.get_or_create(
            machine=self.machine,
            model=gpu_model,
            location=location,
        )
        self.gpus.append({"gpu_card": gpu_card, "gpu_model": gpu_model})
        return gpu_card, gpu_model

    def save_gpus(self):
        for gpu in self.gpus:
            self.save_object(gpu, "gpu_model", "gpu_card")

    def createDrive(self, name, size, interface, manufacturer, serial, partitions):
        physical_disk_model, _ = models.PhysicalDiskModel.objects.get_or_create(
            name=name,
            size=size,
            interface=interface,
            manufacturer=manufacturer
        )

        physical_disk, _ = models.PhysicalDisk.objects.get_or_create(
            machine=self.machine,
            model=physical_disk_model,
            serial=serial,
            partitions=partitions,
        )
        self.physical_disks.append({
            "physical_disk": physical_disk, "physical_disk_model": physical_disk_model
        })
        return physical_disk, physical_disk_model

    def save_physical_disks(self):
        for physical_disk in self.physical_disks:
            self.save_object(physical_disk, "physical_disk_model", "physical_disk")

    def createLogicDisk(self, disk, name, mount, filesystem, size, freesize, disktype):
        logic_disk, _ = models.LogicalDisk.objects.get_or_create(
            disk=disk,
            name=name,
            mount=mount,
            filesystem=filesystem,
            size=size,
            freesize=freesize,
            type=disktype
        )
        self.logic_disks.append(logic_disk)
        return logic_disk

    def save_logic_disks(self):
        for logic_disk in self.logic_disks:
            logic_disk.save()
