### Crutial
- [x] Database (built in options on that, but not anytime soon)
- [ ] Integrate asset handling items as plugins

### Important
- [ ] Make name, cloudID, and computer mac address unique in local DB and
- [ ] Add error handling for local DB stuff
- [ ] Figure out CSV export
- [ ] [WMI RPC control](http://stackoverflow.com/questions/27244056/execute-system-commands-using-wmi-python-on-remote-computer)
- [x] Make data in WMIscan match database data schema
- [x] Instead of skipping the computer already scanned, update it instead in Asset Panda
- [x] Add ability to update computer on database
- [ ] Find out what device and app_version does inside of AssetPanda
- [x] Add way to scan only one computer
- [x] Add error handling for already having asset in AssetPanda (by using `assetpanda.getMachineAssetID()` to add the remoteID to local DB)


### Cleanup
- [ ] Replace --finish command line parameter with automatic detection of incomplete IP addresses from <nmapIP>
- [ ] Add parameters to namp
- [ ] Get network devices once, not twice in WMI
- [ ] Document database design
- [ ] AssetPanda.py's entitydict, fieldsdict to be saved to file and loaded upon library load. Add command line tool to update this file
- [ ] Cleanup program. So many things are statically put in and linked to AssetPanda.
  - [ ] Add a plugin system for asset trackers
- [ ] Config files to specify what you want done
- [x] Better CLI ARGs
- [x] Make AssetPanda support a configuration
- [x] Single settings for integrations (optional extra settings)
- [ ] Document extra settings
- [ ] Seperate code into files (WMI.py, scan.py, etc)
- [ ] Make imports abundantly clear what they're used for (via comments)
- [x] MOAR comments
- [x] Improve and handle more exceptions
- [ ] Make networking exceptions apply every time we reach out
- [ ] Make networking exceptions a tiny library to call across different integrations

### Wishlist
- [ ] Printer support
- [ ] [Linux read support](https://becomelotr.wordpress.com/2013/06/20/managing-linux-via-omi-roadmap/)
- [ ] SNMP support
- [ ] Make argument to skip already scanned computers rather than update it
- [ ] Support for SnipeIT (waiting on RESTful API)
- [x] Support for many WMI authentication credentials
- [ ] HTTPS listener (encryption/auth)

### Long Into The Future
- [ ] Some type of support for OSX/Linux WMIControl
- [ ] GUI Interface
