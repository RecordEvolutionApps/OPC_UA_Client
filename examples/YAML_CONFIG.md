# Example YAML Configuration for OPC UA Client

This file demonstrates how to configure OPCUA_VARIABLES as a multiline YAML property.

## Docker Compose Format

The `docker-compose.example.yml` file shows how to use the pipe `|` operator for multiline strings:

```yaml
environment:
  OPCUA_VARIABLES: |
    [
      {
        "NodeClass": "Variable",
        "NodeId": "ns=2;s=Tank.Temperature",
        "BrowseName": "Temperature"
      }
    ]
```

## Kubernetes ConfigMap Format

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: opcua-client-config
data:
  OPCUA_VARIABLES: |
    [
      {
        "NodeClass": "Variable",
        "NodeId": "ns=2;s=Tank.Temperature",
        "BrowseName": "Temperature",
        "DisplayName": "Tank Temperature"
      },
      {
        "NodeClass": "Variable",
        "NodeId": "ns=2;s=Machine.Voltage",
        "BrowseName": "Voltage"
      }
    ]
```

## Plain YAML File Format

```yaml
# config.yaml
opcua:
  url: "opc.tcp://localhost:4840/opcuaserver"
  namespace: "example:ironflock:com"
  variables: |
    [
      {
        "NodeClass": "Variable",
        "NodeId": "ns=2;s=Tank.Temperature",
        "BrowseName": "Temperature"
      }
    ]
```

## Shell Script with Multiline Variable

```bash
#!/bin/bash

# Option 1: Compact single-line format
export OPCUA_VARIABLES='[{"NodeClass":"Variable","NodeId":"ns=2;s=Tank.Temperature","BrowseName":"Temperature"}]'

# Option 2: Multiline with escaped newlines
export OPCUA_VARIABLES='[
  {
    "NodeClass": "Variable",
    "NodeId": "ns=2;s=Tank.Temperature",
    "BrowseName": "Temperature"
  }
]'

# Option 3: Using heredoc
export OPCUA_VARIABLES=$(cat <<EOF
[
  {
    "NodeClass": "Variable",
    "NodeId": "ns=2;s=Tank.Temperature",
    "BrowseName": "Temperature"
  }
]
EOF
)

docker run -e OPCUA_VARIABLES="$OPCUA_VARIABLES" opcua-client
```

## Important Notes

1. **Whitespace Handling**: The application automatically strips whitespace and handles newlines
2. **JSON Validity**: Ensure the JSON is valid after newlines are removed
3. **YAML Pipe Operator**: Use `|` for literal multiline strings or `>` for folded strings
4. **Escaping**: When setting directly in shell, escape quotes properly

## Supported Formats

Both NodeSet JSON and legacy schema formats work with multiline YAML:

### NodeSet Format (Multiline)
```yaml
OPCUA_VARIABLES: |
  [
    {
      "NodeClass": "Variable",
      "NodeId": "ns=2;s=Tank.Temperature",
      "BrowseName": "Temperature"
    }
  ]
```

### Legacy Schema Format (Multiline)
```yaml
OPCUA_VARIABLES: |
  {
    "Tank": "Temperature",
    "Machine": {
      "Status": "Voltage"
    }
  }
```
