def config_data():

    config={}

    #Provide the ip-address of RPI here
    config['host'] = "192.168.4.44"

    #provide the Username of RPI here
    config['username'] = "ubuntu"

    #Provide the Password of RPI here
    config['password'] = "raspberrypi"

    #Provide the path of example app in the RPI here
    config['path'] = "/home/ubuntu/dut/connectedhomeip/examples/all-clusters-app/linux/out/all-clusters-app"

    return config



