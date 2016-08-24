## Crutial
- [x] Database (built in options on that, but not anytime soon)

### Important
- [ ] Figure out CSV export
- [ ] WMI RPC control
- [ ] Make data in WMIscan match database data schema
- [ ] Instead of skipping the computer already scanned, update it instead in Asset Panda
- [ ] Add ability to update computer on database
- [ ] Rename WMIInfo begining to WMIHandler and have it call WMIAdd or WMIUpdate based on if it is in database
- [ ] Find out what device and app_version does inside of AssetPanda
- [ ] Add way to scan only one computer

### Cleanup
- [ ] Config files to specify what you want done
- [x] Better CLI ARGs
- [x] Make AssetPanda support a configuration
- [x] Single settings for integrations (optional extra settings)
- [ ] Document extra settings
- [ ] Seperate code into files (WMI.py, scan.py, etc)
- [ ] Make imports abundantly clear what they're used for (via comments)
- [ ] MOAR comments
- [ ] Improve and handle more exceptions
- [ ] Make networking exceptions apply every time we reach out
- [ ] Make networking exceptions a tiny library to call across different integrations

#### Wishlist
- [ ] Support for SnipeIT (waiting on RESTful API)
- [ ] NMAP control from program
- [ ] Support for many WMI authentication credentials
- [ ] HTTPS listener (encryption/auth)
- [ ] Make argument to skip already scanned computers rather than update it

##### Long Into The Future
- [ ] Some type of support for OSX/Linux
- [ ] GUI Interface
