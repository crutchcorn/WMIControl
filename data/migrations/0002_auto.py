from __future__ import unicode_literals
from django.core.management import call_command
from django.db import migrations


class Migration(migrations.Migration):

    def load_data(apps, schema_editor):
        call_command("loaddata", "wmiCodes.json")

    dependencies = [
        ('data', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_data),
    ]