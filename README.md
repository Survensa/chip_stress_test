### Example command to run TC_PairUnpair.py

## Raspberrypi 

python3 TC_PairUnpair.py --commissioning-method on-network --discriminator 3840 --passcode 20202021 --storage-path admin_storage.json --number-of-iterations 5 --platform rpi --ipaddress 192.168.4.183 --username ubuntu --password raspberrypi --path /home/ubuntu/master_dut/connectedhomeip/examples/all-clusters-app/linux/out/all-clusters-app

## Nordic Thread

python3 TC_PairUnpair.py --commissioning-method ble-thread --discriminator 3840 --passcode 20202021 --storage-path admin_storage.json --number-of-iterations 20 --platform thread --ble-interface-id 0 --ipaddress 192.168.1.219 --username grl --password chip-cert --path /home/grl --thread-dataset-hex 0e080000000000010000000300001035060004001fffe0020812611111227222220708fd97e1eb459cbbf3051000112433428566778899aabbccddeeff030f4f70656e54687265616444656d6f63010212320410b775feb5fc41b965747da30c8f76bda30c0402a0f7f8
