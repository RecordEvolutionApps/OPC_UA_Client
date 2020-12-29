# OPC UA Client
This is a OPC UA client app which is able to run OPC operations on an OPC UA server.

## Hardware
1. Raspberry Pi registered in RESWARM ([For Detail Click Here](https://reswarm.io/docs/#/en/flash-your-iot-devices))

## Usage Instructions
This app can test connectivity with an OPC UA server by reading the current time node. By default, opc-client is testing the connectivity to opc.tcp://opcplc:50000.


## Install the App
To use the app on your Raspberry Pi, go to RESWARM into the devices menu of the swarm where your device is 
registred ([How To Navigate in RESWARM](https://reswarm.io/docs/#/en/device-management?id=basic-navigation)).
There create a group and add the device to the group and install this app to this group as well 
([Add a New Group](https://reswarm.io/docs/#/en/device-management?id=add-a-new-device-group)). Now the 
device will start downloading the app. 

---

# For Developers
To develop and build the app we are creating a Docker image that can be run on the device. Please check this git repository ([iot-edge-opc-plc](https://github.com/Azure-Samples/iot-edge-opc-plc)) to find detailed information about the OPC UA PLC server.









