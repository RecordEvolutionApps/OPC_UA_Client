import asyncio
from asyncua import Client
from datetime import datetime

class OPCUAClient:
    def __init__(self, endpoint, namespace_name):
        self.endpoint = endpoint
        self.namespace_name = namespace_name
        self.client = Client(endpoint)
        self.namespace_index = None

    async def connect(self):
        """Connect to the OPC UA server and retrieve the namespace index."""
        await self.client.connect()
        self.namespace_index = await self.get_namespace_index(self.namespace_name)

    async def disconnect(self):
        """Disconnect from the OPC UA server."""
        await self.client.disconnect()

    async def get_namespace_index(self, namespace_name):
        """Retrieve the namespace index from the server based on its name."""
        namespaces = await self.client.get_namespace_array()
        print("Namespaces:", namespaces)  # Debug output
        if namespace_name in namespaces:
            return namespaces.index(namespace_name)
        else:
            raise ValueError(f"Namespace '{namespace_name}' not found in server: {namespaces}")

    async def resolve_node_by_full_path(self, path_parts):
        """
        Resolves an OPC UA node using a full hierarchical path (supports deep structures).

        :param path_parts: A list of path components (e.g., ["Device1", "Sensors", "Temperature"]).
        :return: The resolved OPC UA node, or None if not found.
        """
        try:
            # Construct the full path for get_child()
            node_path = ["0:Objects"] + [f"{self.namespace_index}:{part}" for part in path_parts]
            
            # Fetch the node dynamically
            node = await self.client.nodes.root.get_child(node_path)
            print(f"Resolved Path {' → '.join(path_parts)} -> {node.nodeid}")
            return node
        except Exception as e:
            print(f"Failed to resolve path {' → '.join(path_parts)}: {e}")
            return None

    async def extract_leaf_nodes(self, schema, parent_path_parts=None):
        """
        Recursively extract OPC UA variable node paths and dynamically resolve nodes.
        Returns a list of (full_path, node_id, original_schema_reference) tuples.
        """
        if parent_path_parts is None:
            parent_path_parts = []
        
        leaf_nodes_info = []
        
        for key, value in schema.items():
            current_path_parts = parent_path_parts + [key]

            if isinstance(value, dict):
                # If it's a subtree, recurse and extend the list
                leaf_nodes_info.extend(await self.extract_leaf_nodes(value, current_path_parts))
            else:
                variable_path_parts = current_path_parts + [value]
                node = await self.resolve_node_by_full_path(variable_path_parts)
                if node:
                    node_id = node.nodeid
                    full_path = ".".join(variable_path_parts)
                    print(f"Resolved {full_path} -> {node_id}")
                    # Store a reference to where this value should go in the original schema
                    leaf_nodes_info.append((full_path, node_id, current_path_parts, value))
                else:
                    print(f"Warning: Could not resolve {'.'.join(variable_path_parts)} to a node ID.")
            
        return leaf_nodes_info

    async def read_from_schema(self, schema):
        """
        Extract and read data from OPC UA server based on JSON schema,
        retaining the original tree structure.

        :param schema: JSON-like dictionary defining the OPC UA structure.
        :return: Dictionary with timestamp and the schema populated with values.
        """
        print('Reading from schema:', schema)
        tsp = datetime.now().astimezone().isoformat()

        # Create a deep copy of the schema to populate with values
        populated_schema = self._deep_copy_schema(schema)

        # Extract leaf nodes and their original path references
        leaf_nodes_info = await self.extract_leaf_nodes(schema)
        if not leaf_nodes_info:
            print("No leaf nodes found.")
            return {"tsp": tsp, "data": {}}

        # Prepare for bulk reading
        nodes_to_read = []
        path_to_schema_ref = {}

        for full_path, node_id, schema_path_parts, variable_name in leaf_nodes_info:
            nodes_to_read.append(self.client.get_node(node_id))
            # Store a reference back to the exact location in the populated_schema
            path_to_schema_ref[str(node_id)] = (schema_path_parts, variable_name)

        if not nodes_to_read:
            print("No nodes to read after resolution.")
            return {"tsp": tsp, "data": populated_schema} # Return schema with unresolved values if no nodes found

        # Read values from nodes
        values = await self.client.read_values(nodes_to_read)

        # Populate the schema with the read values
        for i, node in enumerate(nodes_to_read):
            node_id_str = str(node.nodeid)
            if node_id_str in path_to_schema_ref:
                schema_path_parts, variable_name = path_to_schema_ref[node_id_str]
                current_level = populated_schema
                # Traverse the populated_schema to the correct location
                for part in schema_path_parts[:-1]:  # Exclude the last part which is the variable key itself
                    current_level = current_level.get(part, {})
                # Assign the value
                if schema_path_parts and schema_path_parts[-1] in current_level:
                    current_level[schema_path_parts[-1]] = values[i]
                else:
                    # This case handles direct assignment if the schema part is the variable name
                    # or if the variable name is the last key in the path_parts
                    # It's a bit tricky because the original schema has the variable name
                    # as the VALUE of the last key, not the key itself.
                    # We need to find the key whose value is `variable_name`
                    # For example, if schema_path_parts is ['Device1', 'Temperature'] and variable_name is 'Value'
                    # We need to set Device1['Temperature'] to the value.
                    # This implies we need to find the KEY in the original schema
                    # whose VALUE was `variable_name`.
                    # The `extract_leaf_nodes` currently returns `current_path_parts` and `value`.
                    # `current_path_parts` includes the key for the variable.
                    # So, if schema_path_parts is ['Device1', 'SensorA'], and value is 'TemperatureValue',
                    # and the original schema was {'Device1': {'SensorA': 'TemperatureValue'}}.
                    # We want populated_schema['Device1']['SensorA'] = actual_value.

                    # Let's adjust the way we store the reference back to the schema
                    # In leaf_nodes_info, we store (full_path, node_id, current_path_parts, value_in_schema)
                    # current_path_parts is ['Device1', 'SensorA']
                    # value_in_schema is 'TemperatureValue'
                    # We need to modify the dictionary at populated_schema['Device1']['SensorA']

                    # Correct logic for assigning value:
                    temp_node = populated_schema
                    for part_idx, part in enumerate(schema_path_parts):
                        if part_idx == len(schema_path_parts) - 1:
                            # This is the key in the populated_schema that we want to update
                            # It corresponds to the 'key' in the original schema: 'SensorA' in our example
                            temp_node[part] = values[i]
                        else:
                            temp_node = temp_node.get(part, {})


        return {"tsp": tsp, "data": populated_schema}

    def _deep_copy_schema(self, schema):
        """Recursively deep copies the schema structure."""
        if isinstance(schema, dict):
            return {k: self._deep_copy_schema(v) for k, v in schema.items()}
        elif isinstance(schema, list):
            return [self._deep_copy_schema(elem) for elem in schema]
        else:
            return None # We will replace this with the actual value

    async def print_all_nodes(self):
        """Print all nodes under the Objects folder."""
        objects_node = self.client.nodes.objects
        children = await objects_node.get_children()
        for child in children:
            print("Node:", child)