# DB models and exceptions
from lib.setSettings import djangopath
djangopath(up=1, settings='settings')
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
from data import models


def listMachines():
    i = 0
    for machine in models.Machine.objects.all():
        i += 1
        print(str(i) + ")", machine.name)
    print("There are", str(i), "number of machines in the database")
