# Collect data from any OPC UA server

The app acts as an OPC UA Client and fetches data from any machine providing a OPC UA interface.
You can specify which data points to read and these are then collected in a structured way in your fleet database.

![screenshot](https://storage.googleapis.com/reswarm-images/OPCUA_collector_screenshot.png)

## Hardware

- (Industrial) PC registered in IronFlock ([For Details on registering devices click here](https://docs.ironflock.com/#/en/Reswarm/reflasher))
- Any modbus server on the same network as the industrial PC.

## Usage Instructions

For setup the edge PC needs a working internet connection, so you can configure it remotely using the IronFlock Platform.
Find your PC in the devices menu, go to the IoT Store and install this app.
You can open the device settings, go the settings of this app and configure it as detailed below:

## Parameters

Parameter | Meaning | Default
--- | --- | ---
OPCUA_URL      | IP address of OPC UA Server for OPC UA Client to listen to | opc.tcp://0.0.0.0:4840/opcuaserver
OPCUA_NAMESPACE    | Namespace under which OPC UA Server is registered          | example:ironflock:com
OPCUA_VARIABLES        | OPC UA (sub)schema that should be extracted and stored     |  {"Tank": "Temperature", "Machine": {"Status": "Voltage"}}
PUBLISH_INTERVAL       | read every x seconds                                     |  2

## OPCUA Value Extraction

In order to define, which variables should be read and published, you can specify a json string.
The json string should be a subtree of the OPCUA schema tree, that is offered by the connected OPCUA server.

```json
{
    "Tank": "Temperature", 
    "Machine": {
        "Status": "Voltage"
        }
}
```

## Data Table Format

The data collected from the OPC UA machine will be stored in the following structure in your fleet database.
You can use this data in any custom dashboard created in your fleet.

```yaml
  - id: tsp
    name: Timestamp
    description: Timestamp of Measurement
    dataType: timestamp
  - id: namespace
    name: Namespace
    description: OPCUA Namespace
    dataType: string
  - id: variable
    name: Variable
    description: OPCUA Variable Name
    dataType: string
  - id: value
    name: Value
    description: OPCUA Variable Value
    dataType: numeric
  - id: devname
    name: Device Name
    description: Name of Edge PC
    dataType: string
```

---

## For Developers

To develop and build the app we are creating a Docker image that can be run on the device. Please check this git repository ([OPCUA Python Library](https://github.com/FreeOpcUa/opcua-asyncio)) to find detailed information about the ***python opcua*** library and some other use cases.

## License

Copyright 2025 Record Evolution GmbH
All rights reserved