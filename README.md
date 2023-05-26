# OPC UA Client
The app acts as an OPC UA Client and fetches data from user specified objects and variable nodes. It also writes data to a named pipe/fifo at every x second.

## Hardware
1. Industrial PC registered in RESWARM ([For Detail Click Here](https://docs.record-evolution.de/#/en/Reswarm/reflasher))

## Usage Instructions
The Industrial PC does need a working Wi-Fi connection, so you can control it remotely using the RESWARM Platform. The app 
tries to connect to an OPC UA Server at ***opc.tcp://0.0.0.0:4840/freeopcua/server/*** by default. 


## Install the App
To use the app on your Industrial PC, go to RESWARM into the devices menu of the swarm where your device is registred.
There create a group and add the device to the group and install this app to this group as well. Now the device will start downloading the app. 


### Writing Data to a File
Depending on the parameter settings below, the data is written into a user specified pipe/fifo. Please use ***File Writer*** app to create a csv or other available format file from the data written into the pipe/fifo.

Respectively, the data written to the named pipe/fifo is of the following format:

```json
{
    "name of 1st variable node": "value of 1st variable node",
    "name of 2nd variable node": "value of 2nd variable node",
    "name of n variable node": "value of 3rd variable node"
}
```

## Parameters

Parameter | Meaning | Default
--- | --- | ---
SERVER_ADDRESS      | IP address of OPC UA Server for OPC UA Client to listen to | opc.tcp://0.0.0.0:4840/freeopcua/server/
LISTEN_NAMESPACE    | Namespace under which OPC UA Server is registered          | OPCUA_SERVER_Reswarm
ENABLE_ENCRYPTION   | Should the communication between OPC UA Server and OPC UA Client be encrypted | True
READ_OBJECTS        | Name of object node/s to be read                           | 
READ_VARIABLES      | Name of variable node/s to be read                         | 
WRITE_TO_PIPE       | Name of output pipe                                        | 

---
The above mentioned parameters are a classic example of a single object and a single variable node. In case the app must be run for multiple objects and variable nodes then the following changes in the parameters can be made:

### For Single Object and Single Variable Nodes
READ_OBJECT_S | Name of object node/s | ["Object_Node_1"]\
READ_VARIABLE_S | Name of variable node/s | [["Variable_1"]]

### For Single Object and Multiple Variable Nodes 
READ_OBJECT_S | Name of object node/s | ["Object_Node_1"]\
READ_VARIABLE_S | Name of variable node/s | [["Variable_1", "Variable_2"]]

### For Multiple Objects and Multiple Variable Nodes 
READ_OBJECT_S | Name of object node/s | ["Object_Node_1", "Object_Node_2"]\
READ_VARIABLE_S | Name of variable node/s | [["Variable_1", "Variable_2"], ["Variable_1", "Variable_2"]]

---

# For Developers
To develop and build the app we are creating a Docker image that can be run on the device. Please check this git repository ([OPCUA Python Library](https://github.com/FreeOpcUa/python-opcua)) to find detailed information about the ***python opcua*** library and some other use cases.









