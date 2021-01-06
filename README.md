# OPC UA Client
The app act as a OPC UA Client in order to recieve data from a OPC UA Server. It publishes the data every
x second to the WAMP router and also write data to a csv file.

## Hardware
1. Raspberry Pi registered in RESWARM ([For Detail Click Here](https://reswarm.io/docs/#/en/flash-your-iot-devices))

## Usage Instructions
The Raspberry Pi does need a working Wifi connection, so you can control it remotely using the RESWARM Platform. The app 
tries to coonect to an OPC UA Server at ***opc.tcp://0.0.0.0:4840/freeopcua/server/*** by default. An error is thrownby the app, in case no OPC UA Server is listining to the default or user defined address.


## Install the App
To use the app on your Raspberry Pi, go to RESWARM into the devices menu of the swarm where your device is 
registred ([How To Navigate in RESWARM](https://reswarm.io/docs/#/en/device-management?id=basic-navigation)).
There create a group and add the device to the group and install this app to this group as well 
([Add a New Group](https://reswarm.io/docs/#/en/device-management?id=add-a-new-device-group)). Now the 
device will start downloading the app. 

### Publishing Data
Depending on the parameter settings below the data will be published to the reswarm WAMP router on the configured topic. You can listen to the topic with a Datapod to receive the data in near-realtime. In order to not disturb the structure/format of the data, the data is not formated/changed at all and published as it recieved by the client. 

The data that is published will be of the following form:

```text
root node name, object name, variable name, value of variable
```

### Writing Data to a File
Depending on the parameter settings below the data is also written as a file into the configured folder. This file then can be moved to other places using other apps like the [AWS S3 Sender](https://reswarm.io/en/apps/AWS_S3_Sender).

Respectively the data written to disk will be a comma seperated csv file of the form:

```text
root node name, object name, variable name, value of variable
```

Internally the data will be read from the OPC UA Server and buffered in memory. The data will be sent as soon as a network connection is available. If no network is available the internal buffer can become very large. After 500000 records in the buffer, the oldest data will be removed when new data is buffered. 

## Parameters

Parameter | Meaning | Default
--- | --- | ---
PUBLISH_DATA | If 'ON' then data will be published | ON
TOPIC_PREFIX | Topic prefix for WAMP publishing. The final topic will be `TOPIC_PREFIX.DEVICE_SERIAL_NUMBER` | reswarm.opc_ua_client
WRITE_FILE | IF 'ON' then files will be written. | ON
DATA_SUBFOLDER | Subfolder under `/shared` to put the output files in. | opc_ua_client
FREQ_DATA_LOG | Frequency in Hertz for data logging | 2
SERVER_ADDRESS | IP address of OPC UA Server for OPC UA Client to listen to | opc.tcp://0.0.0.0:4840/freeopcua/server/
LISTEN_NAMESPACE | Namespace under which OPC UA Server is registered| OPCUA_SERVER_Reswarm
ENABLE_ENCRYPTION | Should the communication between Server and Client be encrypted | True
READ_NODE_S | Name of root node of Server | Node1
READ_OBJECT_S | Name of object node/s | ["ObjectOne", "ObjectTwo"]
READ_VARIABLE_S | Name of variable node/s | [["Timestamp", "Devicename"], ["Temperature", "Volt"]]
MAX_ROWS_PER_FILE | After this many rows a new file will be started | 50
MAX_TIME_PER_FILE | After this many seconds a new file will be started | 30

---
The above mentioned parameters are a classic example of multiple object as well as variable nodes. In case the app must be run for single object and variable parameters then following changes in parameters can be adapted:

#### For Single Object and Single Variable Nodes
READ_OBJECT_S | Name of object node/s | ["ObjectOne"]
READ_VARIABLE_S | Name of variable node/s | [["Timestamp"]]

#### For Single Object and Multiple Variable Nodes 
READ_OBJECT_S | Name of object node/s | ["ObjectOne"]
READ_VARIABLE_S | Name of variable node/s | [["Timestamp", "Devicename"]]

#### For Multiple Objects and Multiple Variable Nodes 
READ_OBJECT_S | Name of object node/s | ["ObjectOne", "ObjectTwo"]
READ_VARIABLE_S | Name of variable node/s | [["Timestamp", "Devicename"], ["Temperature", "Volt"]]

---

# For Developers
To develop and build the app we are creating a Docker image that can be run on the device. Please check this git repository ([OPCUA Python Library](https://github.com/FreeOpcUa/python-opcua)) to find detailed information about the ***python opcua*** library and some other use cases.









