# WMIControl
## Preface
This project's goals are to create a sort of "control center".
This would include WMI scanner, asset management medium, and management software, and more.

### Databases
A database is a way to optimally store a large amount of data and be able to reasonably handle that data and filter, sort, or otherwise manage that data. If you do not have some type of conceptual understanding of databases, I would recommend taking a break from this page to go search a bit more on the concepts of databases.

There are many kinds of databases, but because we are using Django as the Python medium between the program and a backend database, the only supported databases are: PostgreSQL, MySQL, Oracle and SQLite. We personally use PostgreSQL for testing, however it should work the same no matter which one of them you use. Please refer to the documentation there for how to install and setup the root user and normal user of the program. You do not manually need to make a database, as this program will handle that; but you will need to make a normal user.

## Installation
### Prereqs:
- Correct architecture Python 3 installed to PATH
- Git installed to PATH
- Have your database server installed with a user and database set up for WMIControl.

### NMAP
This program requires nmap to be previously installed. Proceed to download from [here](https://nmap.org/download.html). Insure you are downloading and installing the Windows version

### PyWin32
WMIControl uses a library called PyWin32. Unfortunately, it is not unable to be packaged within PyPi. You have to install it from their installer [here](https://sourceforge.net/projects/pywin32/files/pywin32/Build%20220/). Ensure you have to proper architecture selected for your Windows version. You must also have the same arcitecture of Python installed, otherwise you will recieve errors such as:
`PermissionError: [Errno 13] Permission denied: 'C:\\Program Files (x86)\\python\\lib\\site-packages\\win32com\\gen_py\\__init__.py'`

### Commands
```
git clone https://github.com/crutchcorn/WMIControl.git
cd WMIControl
pip install requirements.txt
python manage.py migrate
```

## Configuration
The example configuration file is under `conf.toml.example`. You'll need to copy or rename that file to `conf.toml` and edit it to reflect your settings.
The settings are as follows:
`[credentials]`
Where all of your credentials will stay

`[credentials.wmi]`
Refers to the login information for WMI to authenticate and run it's scans. This will be expanded on later to support many possibilities of authentication credentials

`[credentials.assetpanda]`
Login information that you'll need to supply to use AssetPanda as your asset management software. Please refer to their API documentation for more information. This will eventually be expanded on and used to add other asset tracking  or to disable this option entirely. 

`[db]`
Where all of the Django and database related settings will stay

`secret_key`
This is the... Well... Secret key for Django. Not really helpful explaination, I know - but it's kinda like a password to authenticate with some of the function calls in Django.

`[db.databases]`
Covers the main settings for your database that will be connected to Django, while the rest is fairly straightforard, I will cover what the supported values of `engine`.

`engine`
Covers the backend database system that Django will use.
Supported values are:
```
django.db.backends.postgresql
django.db.backends.mysql
django.db.backends.sqlite3
django.db.backends.oracle
```

## Usage
- `wmicontrol -h` or `wmicontrol --help` - Show the help screen.
- `wmicontrol -v` or `wmicontrol --version` - Show version.
- `wmicontrol scan` - Start a local or remote scan. This will run locally when no arguments follow
- `wmicontrol -r` or `wmicontrol --range` - Scan a range of IP addresses. Followed immediately by the start IP and then by the end IP.
	- EG: `wmicontrol -r 192.168.1.50 192.168.1.100`
- `wmicontrol --subnet=<subnet>` - Scan entire IP subnet.
	- EG: `wmicontrol --subnet=192.168.1`

Currently, the CLI arguments are VERY likely to change and will not be stable until otherwise noted.
