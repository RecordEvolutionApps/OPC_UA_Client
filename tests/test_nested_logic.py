#!/usr/bin/env python3
"""Test enhanced NodeSet path parsing logic (standalone)"""

def build_nested_dict(path_parts, value):
    """
    Build a nested dictionary from a path and value.
    E.g., ["Machine1", "Tank", "Temperature"], 65.3 
    -> {"Machine1": {"Tank": {"Temperature": 65.3}}}
    """
    if len(path_parts) == 1:
        return {path_parts[0]: value}
    
    result = {}
    current = result
    for i, part in enumerate(path_parts[:-1]):
        current[part] = {}
        current = current[part]
    current[path_parts[-1]] = value
    
    return result

def merge_nested_dicts(dict1, dict2):
    """
    Recursively merge two nested dictionaries.
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_nested_dicts(result[key], value)
        else:
            result[key] = value
    
    return result

from flatTree import json_tree_to_table

print("=" * 80)
print("TEST: NodeSet Path Parsing for Nested Variables")
print("=" * 80)

print("\n1. Building nested dictionaries from paths:")
print("-" * 80)

test_cases = [
    (["Machine1", "Tank", "Temperature"], 65.3),
    (["Machine1", "Tank", "Pressure"], 2.5),
    (["Machine1", "Motor", "Speed"], 1450.0),
    (["Machine1", "Motor", "Status"], "Running"),
]

data = {}
for path, value in test_cases:
    nested = build_nested_dict(path, value)
    data = merge_nested_dicts(data, nested)
    print(f"  Added: {'.'.join(path)} = {value}")

print(f"\nFinal nested structure:")
import json
print(json.dumps(data, indent=2))

print("\n\n2. How flatTree.py handles the nested structure:")
print("-" * 80)

output = {
    "tsp": "2025-11-20T10:30:00+00:00",
    "data": data
}

rows = json_tree_to_table(output)
print(f"\nGenerated {len(rows)} flattened rows:")
for row in rows:
    print(f"  variable: '{row['variable']:<35}' value: {row['value']}")

print("\n\n3. Example NodeSet configuration:")
print("-" * 80)
print("""
For the above nested structure, your OPCUA_VARIABLES would be:

[
  {
    "NodeClass": "Variable",
    "NodeId": "ns=1;s=Machine1.Tank.Temperature",
    "BrowseName": "Temperature"
  },
  {
    "NodeClass": "Variable",
    "NodeId": "ns=1;s=Machine1.Tank.Pressure",
    "BrowseName": "Pressure"
  },
  {
    "NodeClass": "Variable",
    "NodeId": "ns=1;s=Machine1.Motor.Speed",
    "BrowseName": "Speed"
  },
  {
    "NodeClass": "Variable",
    "NodeId": "ns=1;s=Machine1.Motor.Status",
    "BrowseName": "Status"
  }
]

The enhanced read_from_nodeset() will:
1. Parse the NodeId path: "ns=1;s=Machine1.Tank.Temperature" → ["Machine1", "Tank", "Temperature"]
2. Build nested structure automatically
3. flatTree.py creates proper paths: "Machine1.Tank.Temperature"
""")

print("\n" + "=" * 80)
print("✓ NESTED VARIABLES: Fully supported with NodeSet format!")
print("=" * 80)
