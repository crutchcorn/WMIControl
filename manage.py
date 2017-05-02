#!/usr/bin/env python
import os
import sys
from django.core.management import execute_from_command_line
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")


def runArgV(args=None):
    if not args:  # Way around mutable default arguments
        args = ['.\\manage.py', 'migrate']
    execute_from_command_line(args)

if __name__ == "__main__":
    runArgV(sys.argv)
