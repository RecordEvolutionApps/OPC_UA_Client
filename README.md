# Collect data from any OPC UA server

This app is an OPC UA Client and fetches data from any machine providing a OPC UA interface.
You can specify which data points to read and these are then collected in a structured way in your fleet database.

<div style="display: flex; justify-content: center;">
    <img src="https://res.cloudinary.com/dk8bhmsdz/image/upload/v1759151728/Screenshot_2025-09-29_at_15.15.05_pweooy.png" width="600px">
</div>

## Hardware

- (Industrial) PC registered in IronFlock ([For Details on registering devices click here](https://docs.ironflock.com/#/en/Reswarm/reflasher))
- Any OPC UA server on the same network as the industrial PC.

## Usage Instructions

For setup the edge PC needs a working internet connection, so you can configure it remotely using the IronFlock Platform.

Go the settings of this app on your device and configure it as detailed below:

## Parameters

Parameter | Meaning | Default
--- | --- | ---
OPCUA_URL      | IP address of OPC UA Server for OPC UA Client to listen to | opc.tcp://0.0.0.0:4840/opcuaserver
OPCUA_NAMESPACE    | Namespace under which OPC UA Server is registered          | example:ironflock:com
OPCUA_VARIABLES        | OPC UA NodeSet JSON or legacy schema to extract and store (supports multiline YAML)     |  [{"NodeClass": "Variable", "NodeId": "ns=2;s=Tank.Temperature", "BrowseName": "Temperature"}]
PUBLISH_INTERVAL       | read every x seconds                                     |  2

**Note:** `OPCUA_VARIABLES` supports multiline YAML format. See [YAML_CONFIG.md](YAML_CONFIG.md) for examples.

## OPCUA Value Extraction

You can specify variables to read in two formats:

### 1. NodeSet JSON Format (Recommended)

Provide an array of OPC UA node definitions following the NodeSet2 XML JSON schema:

```json
[
    {
        "NodeClass": "Variable",
        "NodeId": "ns=2;s=Tank.Temperature",
        "BrowseName": "Temperature",
        "DisplayName": "Tank Temperature"
    },
    {
        "NodeClass": "Variable",
        "NodeId": {"IdType": "String", "Id": "Machine.Voltage", "Namespace": 2},
        "BrowseName": "Voltage"
    }
]
```

You can also provide a single node object instead of an array.

### 2. Legacy Schema Format

The legacy custom schema format is still supported:

```json
{
    "Tank": "Temperature", 
    "Machine": {
        "Status": "Voltage"
    }
}
```

The system automatically detects which format you're using.

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

The data is redundantly stored as a flat key value store as well:

```yaml
  - id: tsp
    name: Timestamp 
    description: Timestamp of Measurement
    path: args[2].tsp
    dataType: timestamp
  - id: namespace
    name: Namespace
    description: OPCUA Namespace
    path: args[0]
    dataType: string
  - id: machine_name
    name: Machine Name
    description: Given Machine Name
    path: args[1]
    dataType: string
  - id: leaf_path
    name: Object Path
    description: "Path to the leaf in the OPC UA data object"
    path: args[2].variable
    dataType: string
  - id: value
    name: Value
    description: OPCUA Data Value
    path: args[2].value
    dataType: string
  - id: devname
    name: Device Name
    description: Name of Device
    path: kwargs.DEVICE_NAME
    dataType: string
```

---


## License

Copyright 2025 Record Evolution GmbH
All rights reserved