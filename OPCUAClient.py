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

        :param schema: JSON-like dictionary defining the OPC UA structure.
        :param parent_path_parts: List of path components leading to the current node.
        :return: List of (full path, node ID) tuples.
        """
        if parent_path_parts is None:
            parent_path_parts = []
        
        leaf_nodes = []
        
        for key, value in schema.items():
            current_path_parts = parent_path_parts + [key]  # Append current key to path

            if isinstance(value, dict):  # If it's a subtree, recurse
                leaf_nodes.extend(await self.extract_leaf_nodes(value, current_path_parts))
            else:
                # Include the variable name in the path
                variable_path_parts = current_path_parts + [value]
                node = await self.resolve_node_by_full_path(variable_path_parts)  # Convert full path to node
                if node:
                    node_id = node.nodeid  # Retrieve the node ID
                    full_path = ".".join(variable_path_parts)  # Create dot-separated path
                    print(f"Resolved {full_path} -> {node_id}")  # Debugging
                    leaf_nodes.append((full_path, node_id))
                else:
                    print(f"Warning: Could not resolve {'.'.join(variable_path_parts)} to a node ID.")
            
        return leaf_nodes

    async def read_from_schema(self, schema):
        """
        Extract and read data from OPC UA server based on JSON schema.

        :param schema: JSON-like dictionary defining the OPC UA structure.
        :return: List of dictionaries containing timestamp, variable path, and value.
        """
        print('Reading from schema:', schema)
        tsp = datetime.now().astimezone().isoformat()

        # Extract leaf nodes and resolve their paths to node IDs
        leaf_nodes = await self.extract_leaf_nodes(schema)
        if not leaf_nodes:
            print("No leaf nodes found.")
            return []

        # Unzip paths and node IDs
        paths, node_ids = zip(*leaf_nodes)

        # Convert node IDs to node objects
        nodes = [self.client.get_node(node_id) for node_id in node_ids]

        # Read values from nodes
        values = await self.client.read_values(nodes)

        # Return data in the desired format
        return [{"tsp": tsp, "variable": path, "value": value} for path, value in zip(paths, values)]

    async def print_all_nodes(self):
        """Print all nodes under the Objects folder."""
        objects_node = self.client.nodes.objects
        children = await objects_node.get_children()
        for child in children:
            print("Node:", child)

