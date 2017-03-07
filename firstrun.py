from shutil import copy2 as copy
import os
import json
from sys import exit


def main():
    with open('flags.json') as flagsJSON:
        flags = json.load(flagsJSON)

    if flags['finishedFirstRun'] is False:
        configfilelocation = os.path.join(os.path.expanduser('~'), "conf.toml")
        examplefilelocation = os.path.join(os.path.expanduser('~'), "conf.toml.example")
        if not os.path.isfile(configfilelocation):
            if os.path.isfile(examplefilelocation):
                print("Example config file found at " + examplefilelocation)
                print("Please copy this file to " + configfilelocation + " and modify it to match your settings")
                exit()
            else:
                print("Config file not found, creating example config file.")
                print("Please find the file and copy it to conf.toml and modify the proper settings")
                copy("conf.toml.example", os.path.expanduser('~'))
                print("File is found at " + configfilelocation)
                exit()
        else:
            print("Using config file found at " + configfilelocation)
            flags['finishedFirstRun'] = True
            with open('flags.json', 'w') as f:
                json.dump(flags, f)
