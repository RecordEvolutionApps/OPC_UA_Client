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
            # print(f"Resolved Path {' → '.join(path_parts)} -> {node.nodeid}")
            return node
        except Exception as e:
            print(f"Failed to resolve path {' → '.join(path_parts)}: {e}")
            return None

    async def extract_leaf_nodes(self, schema, parent_path_parts=None):
        """
        Recursively extract OPC UA variable node paths and dynamically resolve nodes.
        Returns a list of (full_opcua_path_string, node_id, schema_parent_path, schema_key_for_variable, opcua_variable_name) tuples.
        """
        if parent_path_parts is None:
            parent_path_parts = []
        
        leaf_nodes_info = []
        
        for key, value in schema.items():
            # This 'key' is the one we want to keep in the final output, e.g., "Tank" or "Status"
            current_schema_key = key 
            current_schema_parent_path = parent_path_parts # The path to the parent of 'current_schema_key'

            if isinstance(value, dict):
                # If it's a subtree, recurse and extend the list
                leaf_nodes_info.extend(await self.extract_leaf_nodes(value, parent_path_parts + [current_schema_key]))
            else:
                # 'value' is the OPC UA variable name (e.g., "Temperature", "Voltage")
                opcua_variable_name = value 
                
                # The full path to the OPC UA node includes the schema path and the OPC UA variable name
                # E.g., if schema_path is ['Tank'] and opcua_variable_name is 'Temperature', OPC UA path might be ['Tank', 'Temperature']
                opcua_full_path_parts = parent_path_parts + [current_schema_key, opcua_variable_name]
                
                node = await self.resolve_node_by_full_path(opcua_full_path_parts)
                if node:
                    node_id = node.nodeid
                    full_opcua_path_string = ".".join(opcua_full_path_parts)
                    # print(f"Resolved {full_opcua_path_string} -> {node_id}")
                    # Store (OPC UA full path string, NodeId, parent path in original schema, key for this variable, actual OPC UA variable name)
                    leaf_nodes_info.append((full_opcua_path_string, node_id, current_schema_parent_path, current_schema_key, opcua_variable_name))
                else:
                    print(f"Warning: Could not resolve {'.'.join(opcua_full_path_parts)} to a node ID.")
            
        return leaf_nodes_info

    async def read_from_schema(self, schema):
        """
        Extract and read data from OPC UA server based on JSON schema,
        retaining the original tree structure and populating with values.

        :param schema: JSON-like dictionary defining the OPC UA structure.
        :return: Dictionary with timestamp and the schema populated with values.
        """
        # print('Reading from schema:', schema)
        tsp = datetime.now().astimezone().isoformat()

        # Create a deep copy of the schema to populate with values
        populated_schema = self._deep_copy_schema(schema)

        # Extract leaf nodes and their original path references
        # leaf_nodes_info will contain (full_opcua_path_string, node_id, schema_parent_path, schema_key_for_variable, opcua_variable_name) tuples.
        leaf_nodes_info = await self.extract_leaf_nodes(schema)
        if not leaf_nodes_info:
            print("No leaf nodes found.")
            return {"tsp": tsp, "data": populated_schema} # Return schema with unresolved values if no nodes found

        # Prepare for bulk reading
        nodes_to_read = []
        node_id_to_schema_info = {}

        for full_opcua_path_string, node_id, schema_parent_path, schema_key_for_variable, opcua_variable_name in leaf_nodes_info:
            nodes_to_read.append(self.client.get_node(node_id))
            # Store a reference back to the exact location in the populated_schema
            node_id_to_schema_info[str(node_id)] = (schema_parent_path, schema_key_for_variable, opcua_variable_name)

        if not nodes_to_read:
            print("No nodes to read after resolution.")
            return {"tsp": tsp, "data": populated_schema}

        # Read values from nodes
        values = await self.client.read_values(nodes_to_read)

        # Populate the schema with the read values
        for i, node in enumerate(nodes_to_read):
            node_id_str = str(node.nodeid)
            if node_id_str in node_id_to_schema_info:
                schema_parent_path, schema_key_for_variable, opcua_variable_name = node_id_to_schema_info[node_id_str]
                read_value = values[i]

                current_level = populated_schema
                # Traverse to the parent dictionary where the 'schema_key_for_variable' resides
                for part_key in schema_parent_path:
                    current_level = current_level.get(part_key)

                # Now, at 'current_level', 'schema_key_for_variable' (e.g., "Tank" or "Status")
                # is the key we want to update.
                # The value for this key should be a new dictionary like {"Temperature": 23.33}
                current_level[schema_key_for_variable] = {opcua_variable_name: read_value}

        return {"tsp": tsp, "data": populated_schema}

    def _deep_copy_schema(self, schema):
        """Recursively deep copies the schema structure, preparing for population."""
        if isinstance(schema, dict):
            return {k: self._deep_copy_schema(v) for k, v in schema.items()}
        elif isinstance(schema, list):
            return [self._deep_copy_schema(elem) for elem in schema]
        else:
            # For leaf nodes (strings representing variable names),
            # we just return None initially. This will be overwritten with a dict.
            return None

    async def print_all_nodes(self):
        """Print all nodes under the Objects folder."""
        objects_node = self.client.nodes.objects
        children = await objects_node.get_children()
        for child in children:
            print("Node:", child)