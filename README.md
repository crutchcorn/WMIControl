# WMIControl
This project's goals are to create a sort of "control center".
This would include WMI scanner, asset management medium, and management software, and more.

## Installation
###### Assuming using Windows, git installed, and using Python 3 in path
```
git clone https://github.com/crutchcorn/WMIControl.git
cd WMIControl
pip install requirements.txt
```

## Usage
`python main.py`

Should output generally how to use the program. For more information, you can pass through the `-h` flag to display help. Currently, the CLI arguments are VERY likely to change and will not be stable until otherwise noted.

#### I made a boom. How do I start over?
```
DROP DATABASE wmicontrol;
CREATE DATABASE wmicontrol WITH OWNER wmicontrol;
```