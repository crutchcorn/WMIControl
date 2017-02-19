
# Core imports
import os

# Database info
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

# DB models and exceptions
from data import models

processor_string = "processor"
cpu_model_string = "cpu_model"
ram_stick_string = "ram_stick"
ram_model_string = "ram_model"
gpu_card_string = "gpu_card"
gpu_model_string = "gpu_model"
network_card_string = "network_card"
network_model_string = "network_model"
physical_disk_model_string = "physical_disk_model"
physical_disk_string = "physical_disk"


class Machine:
    """ To pass through items, you can consider it assigned as such
    self.processors = [{processor_string: processors, "cpu_model": cpu_models}]
    self.rams = [{"ram_stick": ram_sticks, "ram_model": ram_models}]
    self.gpus = [{"gpu_card": gpu_cards, "gpu_model": gpu_models}]
    self.networks = [{"network_card": network_cards, "network_model": network_models}]
    self.physical_disks = [{"physical_disk_model": physical_disk_models, "physical_disk": physical_disks}]
    """
    def __init__(self, machine=models.Machine(), model=models.MachineModel(), processors=None, rams=None, gpus=None,
                 networks=None, physical_disks=None, logic_disks=None):
        self.machine = machine
        self.model = model
        if processors:
            self.processors = processors
        else:
            self.processors = []
        if rams:
            self.rams = rams
        else:
            self.rams = []
        if gpus:
            self.gpus = gpus
        else:
            self.gpus = []
        if networks:
            self.networks = networks
        else:
            self.networks = []
        if physical_disks:
            self.physical_disks = physical_disks
        else:
            self.physical_disks = []
        if logic_disks:
            self.logic_disks = logic_disks
        else:
            self.logic_disks = []

    def save(self):
        self.model.save()
        self.machine.save()
        self.save_gpus()
        self.save_networks()
        self.save_physical_disks()
        self.save_processors()
        self.save_rams()
        return self.machine

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

        self.processors.append({processor_string: processor, cpu_model_string: cpu_model})
        return processor, cpu_model

    @staticmethod
    def save_processor(processor):
        processor[cpu_model_string].save()
        processor[processor_string].save()

    def save_processors(self):
        for processor in self.processors:
            self.save_processor(processor)

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
        self.rams.append({ram_stick_string: ram_stick, ram_model_string: ram_model})
        return ram_stick, ram_model

    @staticmethod
    def save_ram(ram):
        ram[ram_model_string].save()
        ram[ram_stick_string].save()

    def save_rams(self):
        for ram in self.rams:
            self.save_ram(ram)

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
        self.networks.append({network_card_string: network_card, network_model_string: network_model})
        return network_card, network_model

    @staticmethod
    def save_network(network):
        network[network_model_string].save()
        network[network_card_string].save()

    def save_networks(self):
        for network in self.networks:
            self.save_network(network)

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
        self.gpus.append({gpu_card_string: gpu_card, gpu_model_string: gpu_model})
        return gpu_card, gpu_model

    @staticmethod
    def save_gpu(gpu):
        gpu[gpu_model_string].save()
        gpu[gpu_card_string].save()

    def save_gpus(self):
        for gpu in self.gpus:
            self.save_gpu(gpu)

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
            physical_disk_string: physical_disk, physical_disk_model_string: physical_disk_model
        })
        return physical_disk, physical_disk_model

    @staticmethod
    def save_physical_disk(physical_disk):
        physical_disk[physical_disk_model_string].save()
        physical_disk[physical_disk_string].save()

    def save_physical_disks(self):
        for physical_disk in self.physical_disks:
            self.save_physical_disk(physical_disk)

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
