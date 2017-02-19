# Core imports
import os

# Database info
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

# DB models and exceptions
from data import models

class Machine:
    # Constructor
    def __init__(self, machine=models.Machine(), model=models.MachineModel(), cpu_model=models.CPUModel(),
                 processor=models.CPU(), ram_model=models.RAMModel(), ram_stick=models.RAM(),
                 gpu_model=models.GPUModel(), gpu_card=models.GPU(),
                 network_model=models.NetworkModel(), network_card=models.Network()):
        self.machine = machine
        self.model = model
        self.cpu_model = cpu_model
        self.processor = processor
        self.ram_model = ram_model
        self.ram_stick = ram_stick
        self.gpu_model = gpu_model
        self.gpu_card = gpu_card
        self.network_model = network_model
        self.network_card = network_card

    def save(self):
        self.model.save()
        self.machine.save()