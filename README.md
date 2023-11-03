### Example command to run TC_PairUnpair.py
Before running the commands, we need to setup the essential packages which will be done by running the command
                   ```python setup.py install```
After this command installs the neccessary packages we can start with usage of script
## Raspberrypi 

```python TC_PairUnpair.py --discriminator 3840 --passcode 20202021 --storage-path admin_storage.json --yaml-file <path to yaml file>```

## Nordic Thread

python3 TC_PairUnpair.py --discriminator 3840 --passcode 20202021 --storage-path admin_storage.json --ble-interface-id 0  --thread-dataset-hex 0e080000000000010000000300001035060004001fffe0020812611111227222220708fd97e1eb459cbbf3051000112433428566778899aabbccddeeff030f4f70656e54687265616444656d6f63010212320410b775feb5fc41b965747da30c8f76bda30c0402a0f7f8 --yaml-file <path-to-yaml-file>
### About Script

The scripts in the repo are used to pair and unpair with DUT several number of times. Currently the script assumes two simulated modes of DUT.The first type is raspberrpi device acting as DUT using the all-clusters-app and the second one is using the nRf52840-DK development thread board.

If the nRf52840-DK device is used then user should make sure to give the location of the  when prompted by terminal override.py as this will be the script to advertise and reset the DUT along with a few other functions.
