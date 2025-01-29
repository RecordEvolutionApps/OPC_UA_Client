# OPC UA Client

The app acts as an OPC UA Client and fetches data from user specified objects and variable nodes.
The variables read are then published to the IronFlock platform.

## Hardware

1. Industrial PC registered in IronFlock ([For Detail Click Here](https://docs.ironflock.com/#/en/Reswarm/reflasher))

## Usage Instructions

The Industrial PC does need a working Wi-Fi connection, so you can control it remotely using the IronFlock Platform. The app tries to connect to an OPC UA Server at ***opc.tcp://0.0.0.0:4840/opcuaserver*** by default.

## Install the App

To use the app on your Industrial PC, go to IronFlock into the devices menu of the swarm where your device is registred.
There create a group and add the device to the group and install this app to this group as well. Now the device will start downloading the app.

## Parameters

Parameter | Meaning | Default
--- | --- | ---
OPCUA_URL      | IP address of OPC UA Server for OPC UA Client to listen to | opc.tcp://0.0.0.0:4840/opcuaserver
OPCUA_NAMESPACE    | Namespace under which OPC UA Server is registered          | example:ironflock:com
OPCUA_VARIABLES        | Object and Variable names which should be read & published     |  '{"Tank": "Temperature"}'
PUBLISH_INTERVAL       | read and publish every x seconds                                     |  3

## OPCUA Variables

In order to define, which variables should be read and published, you can specify a json string.
The json string can contain multiple OPCUA Object names. Each Object can contain 1 order more Variables:

```json
{"object1": ["MyVariable1", "MyVariable2"], "obj2": ["var1"], "obj3": "somevar"}
```

---

## For Developers

To develop and build the app we are creating a Docker image that can be run on the device. Please check this git repository ([OPCUA Python Library](https://github.com/FreeOpcUa/opcua-asyncio)) to find detailed information about the ***python opcua*** library and some other use cases.