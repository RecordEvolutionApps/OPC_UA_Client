#!/usr/bin/env python3
"""
Demonstrates handling nested OPC UA variables with both extraction methods.

Example nested OPC UA structure:
  Objects/
    Machine1/
      Tank/
        Temperature (Variable)
        Pressure (Variable)
      Motor/
        Speed (Variable)
        Status (Variable)
"""

from flatTree import json_tree_to_table

print("=" * 80)
print("NESTED OPC UA VARIABLES - Extraction and Flattening Examples")
print("=" * 80)

# ============================================================================
# METHOD 1: Legacy Schema Format
# ============================================================================
print("\n1. LEGACY SCHEMA FORMAT")
print("-" * 80)

# Define the schema matching the OPC UA hierarchy
legacy_schema_config = """
{
    "Machine1": {
        "Tank": {
            "Temperature": "Temperature",
            "Pressure": "Pressure"
        },
        "Motor": {
            "Speed": "Speed",
            "Status": "Status"
        }
    }
}
"""

print("Configuration (OPCUA_VARIABLES):")
print(legacy_schema_config)

# This is what read_from_schema() would return
legacy_output = {
    "tsp": "2025-11-20T10:30:00+00:00",
    "data": {
        "Machine1": {
            "Tank": {
                "Temperature": {"Temperature": 65.3},  # Last level is variable name: value
                "Pressure": {"Pressure": 2.5}
            },
            "Motor": {
                "Speed": {"Speed": 1450.0},
                "Status": {"Status": "Running"}
            }
        }
    }
}

print("\nOutput from read_from_schema():")
print(legacy_output)

print("\nFlattened by flatTree.py:")
legacy_rows = json_tree_to_table(legacy_output)
for row in legacy_rows:
    print(f"  variable: '{row['variable']:<35}' value: {row['value']}")

# ============================================================================
# METHOD 2: NodeSet Format (Flat - loses hierarchy)
# ============================================================================
print("\n\n2. NODESET FORMAT (FLAT - Current Implementation)")
print("-" * 80)

nodeset_flat_config = """
[
    {
        "NodeClass": "Variable",
        "NodeId": "ns=1;s=Machine1.Tank.Temperature",
        "BrowseName": "Temperature",
        "DisplayName": "Temperature"
    },
    {
        "NodeClass": "Variable",
        "NodeId": "ns=1;s=Machine1.Tank.Pressure",
        "BrowseName": "Pressure",
        "DisplayName": "Pressure"
    },
    {
        "NodeClass": "Variable",
        "NodeId": "ns=1;s=Machine1.Motor.Speed",
        "BrowseName": "Speed",
        "DisplayName": "Speed"
    },
    {
        "NodeClass": "Variable",
        "NodeId": "ns=1;s=Machine1.Motor.Status",
        "BrowseName": "Status",
        "DisplayName": "Status"
    }
]
"""

print("Configuration (OPCUA_VARIABLES):")
print(nodeset_flat_config)

# Current implementation: flat output (loses hierarchy)
nodeset_flat_output = {
    "tsp": "2025-11-20T10:30:00+00:00",
    "data": {
        "Temperature": 65.3,
        "Pressure": 2.5,
        "Speed": 1450.0,
        "Status": "Running"
    }
}

print("\nCurrent output from read_from_nodeset():")
print(nodeset_flat_output)

print("\nFlattened by flatTree.py:")
nodeset_flat_rows = json_tree_to_table(nodeset_flat_output)
for row in nodeset_flat_rows:
    print(f"  variable: '{row['variable']:<35}' value: {row['value']}")

print("\n⚠️  PROBLEM: Hierarchy is lost! 'Temperature' and 'Pressure' are ambiguous.")

# ============================================================================
# METHOD 3: NodeSet Format (Enhanced - preserves hierarchy)
# ============================================================================
print("\n\n3. NODESET FORMAT (ENHANCED - Preserves Hierarchy)")
print("-" * 80)

print("Configuration: Same as Method 2")

# Enhanced implementation: parse NodeId path to build hierarchy
nodeset_nested_output = {
    "tsp": "2025-11-20T10:30:00+00:00",
    "data": {
        "Machine1": {
            "Tank": {
                "Temperature": 65.3,
                "Pressure": 2.5
            },
            "Motor": {
                "Speed": 1450.0,
                "Status": "Running"
            }
        }
    }
}

print("\nEnhanced output from read_from_nodeset() (with path parsing):")
print(nodeset_nested_output)

print("\nFlattened by flatTree.py:")
nodeset_nested_rows = json_tree_to_table(nodeset_nested_output)
for row in nodeset_nested_rows:
    print(f"  variable: '{row['variable']:<35}' value: {row['value']}")

print("\n✓ SOLUTION: Hierarchy preserved! Full paths like 'Machine1.Tank.Temperature'")

# ============================================================================
# Summary
# ============================================================================
print("\n\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("""
For NESTED OPC UA variables, you have three options:

1. Legacy Schema Format (current support)
   ✓ Preserves hierarchy explicitly
   ✓ Works perfectly with flatTree.py
   ✗ Requires manual schema definition

2. NodeSet Format - Current Implementation
   ✓ Standard OPC UA format
   ✗ Loses hierarchy (flat BrowseName only)
   ✗ Ambiguous variable names

3. NodeSet Format - Enhanced (RECOMMENDED)
   ✓ Standard OPC UA format
   ✓ Automatically preserves hierarchy from NodeId path
   ✓ Works perfectly with flatTree.py
   ✓ No manual schema needed

RECOMMENDATION: Enhance read_from_nodeset() to parse the NodeId path
(e.g., "ns=1;s=Machine1.Tank.Temperature") and build nested structure.
""")
