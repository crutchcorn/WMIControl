# WMIControl
[![Code Climate](https://codeclimate.com/github/crutchcorn/WMIControl/badges/gpa.svg)](https://codeclimate.com/github/crutchcorn/WMIControl)
## Preface
At it's current state, the program is only able to use WMI to scan Windows machines into a central database for asset tracking. 

### Roadmap

This project's goals are to create a sort of "control center". This would include:
- WMI Scanner
- SNMP Scanner
- Asset Management Web GUI
- Asset Control Web GUI


And more

Though the program is only currently able to do WMI Scanning via the CLI, the code in order to control those machines have been written but are not exposed to the CLI tool.

## Installation
### Prereqs:
- A database installed with login credentials setup, etc
- Correct architecture Python 3 installed and added to PATH
- Git installed to PATH (only for commands below and to sync with the repo for updates)
- Have your database server installed with a user and database set up for WMIControl.

#### Database:
We are using Django ORM to convert models into objects. Django supports the following databases:
- **PostgreSQL**
- **MySQL**
- **Oracle**
- **SQLite**

We personally use PostgreSQL for testing, but it should work the same no matter which one of them you use. Please defer to [Django's documentation](https://docs.djangoproject.com/) for installation and setup.

#### NMAP
This program requires nmap to be previously installed. Proceed to download from [here](https://nmap.org/download.html). Insure you are downloading and installing the Windows version

### Install Commands
```
git clone https://github.com/crutchcorn/WMIControl.git
cd WMIControl
pip install -r requirements.txt
python main.py
```
The program will then generate an `conf.toml.example` file for you to use for a real config file. See below for more
## Configuration
**The example configuration file will be under `%USERPROFILE%\conf.toml.example`. You'll need to copy or rename that file to `conf.toml` and edit it to reflect your settings.**

In order to use WMIControl, you'll need to modify the configuration file to match your settings. The settings are as follows:

**`[settings]`**

`skipUpdate`
This option, if `true`, will allow you to skip updating assets that have already been added to your database. While this may outdate some information, it will allow scans to go much quicker.

`silentlyFail`
This option, if `true`, will allow you to silence any non-max-level-crutial errors while scanning. While this may make scans less reliable, it will allow scans to go much quicker.

___

**`[credentials]`**
A collection of settings where all of your credentials will stay.

`[credentials.wmi]`
Refers to the login information for WMI to authenticate and run it's scans. While this only currently supports usernames and passwords, this will be expanded on later to support many possibilities of authentication credential settings on a per user basis

`[credentials.assetpanda]`
Login information that you'll need to supply to use AssetPanda as your asset management software. Please refer to their API documentation for more information. This will be removed in the future and changed to be more modular.

___

**`[db]`**
Where all of the Django and database related settings will stay

`secret_key`

**Keep this value secret.**

A secure cryptographic key used for signing and other things within Django.

[Running Django with a known secret key defeats many of Django’s security protections, and can lead to privilege escalation and remote code execution vulnerabilities.](https://docs.djangoproject.com/en/1.10/ref/settings/#secret-key)


`[db.databases]`

Covers the main settings for your database that will be connected to Django, while the rest is fairly straightforard, I will cover what the supported values of `engine`.


`engine`

Covers the backend database system that Django will use.
Supported[~1~](https://docs.djangoproject.com/en/1.10/ref/settings/#engine) values are:
```
django.db.backends.postgresql
django.db.backends.mysql
django.db.backends.sqlite3
django.db.backends.oracle
```


While the TOML standard does not require you to define the head of the category if there are no variables in the root, it is best for organizational reasons. Please follow the suggested styling for contributions.

## Usage
While the help page for the program is more than enough to see program usage, here are a few commands to note.

- `wmicontrol -h` or `wmicontrol --help` - Show the help screen.
- `wmicontrol -v` or `wmicontrol --version` - Show version.

Please note; currently, the CLI arguments are VERY likely to change and will not be stable until a v1.0.0 stable release.


# Developer Notes
## Remote CMD
Due to WMI limitations, interactive CMD processes cannot be created. To work around this, we are simulating a CMD instance using Python. The process goes as follows:
Run command, output to file, then display file contents, repeat until "exit"
We will be using the `cmd` module of Python to handle the impersonation of an interactive Windows `cmd` thread
