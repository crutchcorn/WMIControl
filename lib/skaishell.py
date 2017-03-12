import cmd
from importtools.general import listMachines
from importtools.activations.handler import importCSV, retireCSV, searchActivation
import os
import toml

with open(os.path.join(os.path.expanduser('~'), "conf.toml")) as conffile:
    config = toml.loads(conffile.read())


class SkaiShell(cmd.Cmd):
    prompt = 'SKAI:\\ '
    intro = "Skai - For those hard to reach servers."
    doc_header = 'Documented functions (type `help <command>`)'
    misc_header = 'Other functions'
    undoc_header = 'Undocumented functions'
    ruler = '-'

    importUsage = "Usage: import <dbtable> <file>"

    def do_import(self, arguments):
        args = arguments.split(" ")
        if len(args) >= 2:
            if args[0] == "Activation":
                importCSV(os.path.abspath(args[1]))
            else:
                print("I'm sorry, that has not been implamented yet")
        else:
            print(self.importUsage)

    def help_import(self):
        print("Given a formatted csv, import items from a database table")
        print(self.importUsage)

    retireUsage = "Usage: retire <dbtable> <file>"

    def do_retire(self, arguments):
        args = arguments.split(" ")
        if len(args) >= 2:
            if args[0] == "Activation":
                retireCSV(os.path.abspath(args[1]), config['silentlyFail'])
            else:
                print("I'm sorry, that has not been implamented yet")
        else:
            print(self.retireUsage)

    def help_retire(self):
        print("Given a formatted csv, retire items from a database table")
        print(self.retireUsage)

    searchUsage = "Usage: search <dbtable> <field> <value>"

    def do_search(self, arguments):
        args = arguments.split(" ")
        if len(args) >= 3:
            if args[0] == "Activation":
                if args[1] == "mac":
                    searchActivation("mac", args[2])
                if args[1] == "coa":
                    searchActivation("coa", args[2])
                if args[1] == "prodkey":
                    searchActivation("prodkey", args[2])
            else:
                print("I'm sorry, that has not been implamented yet")
        else:
            print(self.searchUsage)

    def help_search(self):
        print("Searches the database for a table's information")
        print(self.searchUsage)

    def do_list(self, line):
        listMachines()

    def help_list(self):
        print("Lists machines currently in your database")
        print("Usage: list")

    def do_exit(self, line):
        return True

    def help_exit(self):
        print("Exits Program")
        print("Usage: exit")

if __name__ == '__main__':
    SkaiShell().cmdloop()
