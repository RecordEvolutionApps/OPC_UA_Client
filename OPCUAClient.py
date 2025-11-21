import logging
from asyncua import Client
from datetime import datetime

logger = logging.getLogger(__name__)

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
        logger.debug(f"Available namespaces: {namespaces}")
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
            logger.debug(f"Resolved Path {' → '.join(path_parts)} -> {node.nodeid}")
            return node
        except Exception as e:
            logger.warning(f"Failed to resolve path {' → '.join(path_parts)}: {e}")
            return None

    def _extract_namespace_from_nodeset(self, nodeset):
        """
        Extract namespace URI from NodeSet JSON if present.
        Returns the first namespace URI from NamespaceUris array, or None.
        """
        # Handle dict with NamespaceUris key
        if isinstance(nodeset, dict) and "NamespaceUris" in nodeset:
            uris = nodeset.get("NamespaceUris", [])
            if uris and len(uris) > 0:
                return uris[0]  # Return first custom namespace
        return None

    def _parse_nodeid(self, nodeid_str):
        """
        Parse a NodeId string (e.g., 'ns=2;i=1001' or 'ns=2;s=Tank.Temperature').
        Returns a tuple (namespace_index, identifier).
        """
        if isinstance(nodeid_str, dict):
            # Handle NodeId as dict: {"IdType": "String", "Id": "Tank.Temperature", "Namespace": 2}
            ns = nodeid_str.get("Namespace", 0)
            id_val = nodeid_str.get("Id")
            return (ns, id_val)
        
        # Parse string format: "ns=2;i=1001" or "ns=2;s=Tank.Temperature"
        parts = nodeid_str.split(";")
        ns = 0
        identifier = None
        
        for part in parts:
            if part.startswith("ns="):
                ns = int(part.split("=")[1])
            elif part.startswith(("i=", "s=", "g=", "b=")):
                identifier = part.split("=", 1)[1]
        
        return (ns, identifier)

    async def extract_variable_nodes_from_nodeset(self, nodeset):
        """
        Extract variable nodes from a NodeSet JSON structure.
        Returns a list of (browse_name, node_id, display_name) tuples for Variable nodes.
        
        :param nodeset: List of node dictionaries from NodeSet JSON, or full NodeSet with UAVariables
        :return: List of (browse_name, node_obj, display_name) tuples
        """
        variable_nodes = []
        
        # Handle full NodeSet structure with UAVariables key
        if isinstance(nodeset, dict) and "UAVariables" in nodeset:
            nodes = nodeset.get("UAVariables", [])
        # Handle both array and single node
        elif isinstance(nodeset, list):
            nodes = nodeset
        else:
            nodes = [nodeset]
        
        for node_def in nodes:
            # Check if this is a Variable node
            node_class = node_def.get("NodeClass", "")
            
            if node_class == "Variable" or node_class == 2:  # 2 is Variable in numeric form
                node_id_def = node_def.get("NodeId")
                browse_name = node_def.get("BrowseName", "")
                display_name = node_def.get("DisplayName", browse_name)
                
                # Handle BrowseName as dict or string
                if isinstance(browse_name, dict):
                    browse_name = browse_name.get("Name", "")
                if isinstance(display_name, dict):
                    display_name = display_name.get("Text", browse_name)
                
                if not node_id_def:
                    logger.warning(f"Node {browse_name} has no NodeId, skipping")
                    continue
                
                # Try to get the node from the server
                try:
                    ns, identifier = self._parse_nodeid(node_id_def)
                    
                    # Use the namespace index from the connection, not from the NodeId
                    # (the NodeId might have a different index than what the server assigned)
                    actual_ns = self.namespace_index if self.namespace_index is not None else ns
                    
                    # Determine if identifier is integer or string
                    if isinstance(identifier, str) and identifier.isdigit():
                        # Integer identifier
                        node_obj = self.client.get_node(f"ns={actual_ns};i={identifier}")
                    else:
                        # String identifier
                        node_obj = self.client.get_node(f"ns={actual_ns};s={identifier}")
                    
                    variable_nodes.append((browse_name, node_obj, display_name))
                    logger.debug(f"Found variable node: {browse_name} (ns={actual_ns};i={identifier})")
                except Exception as e:
                    logger.warning(f"Could not resolve node {browse_name} ({node_id_def}): {e}")
        
        return variable_nodes

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
                    logger.debug(f"Resolved {full_opcua_path_string} -> {node_id}")
                    # Store (OPC UA full path string, NodeId, parent path in original schema, key for this variable, actual OPC UA variable name)
                    leaf_nodes_info.append((full_opcua_path_string, node_id, current_schema_parent_path, current_schema_key, opcua_variable_name))
                else:
                    logger.warning(f"Could not resolve {'.'.join(opcua_full_path_parts)} to a node ID")
            
        return leaf_nodes_info

    def _build_nested_dict(self, path_parts, value):
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
    
    def _merge_nested_dicts(self, dict1, dict2):
        """
        Recursively merge two nested dictionaries.
        """
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_nested_dicts(result[key], value)
            else:
                result[key] = value
        
        return result

    async def read_from_nodeset(self, nodeset):
        """
        Extract and read data from OPC UA server based on NodeSet JSON structure.
        
        :param nodeset: NodeSet JSON structure (list of node definitions)
        :return: Dictionary with timestamp and data populated with values.
        """
        tsp = datetime.now().astimezone().isoformat()
        data = {}
        
        # Extract variable nodes from the NodeSet
        variable_nodes = await self.extract_variable_nodes_from_nodeset(nodeset)
        
        if not variable_nodes:
            logger.warning("No variable nodes found in NodeSet")
            return {"tsp": tsp, "data": data}
        
        # Prepare for bulk reading
        nodes_to_read = [node_obj for _, node_obj, _ in variable_nodes]
        
        # Read values directly from each node
        values = []
        for node in nodes_to_read:
            try:
                value = await node.read_value()
                values.append(value)
                logger.info(f"Read value from {node.nodeid}: {value} (type: {type(value)})")
            except Exception as e:
                logger.warning(f"Failed to read value from {node.nodeid}: {e}")
                values.append(None)
        
        logger.info(f"Read {len(values)} values from {len(nodes_to_read)} nodes")
        for i, ((_browse_name, node_obj, _display_name), value) in enumerate(zip(variable_nodes, values)):
            logger.info(f"Node {node_obj.nodeid}: value = {value}, type = {type(value)}")
        
        # Build nested structure from NodeSet
        for i, (browse_name, _node_obj, display_name) in enumerate(variable_nodes):
            value = values[i]
            
            # Get the original node definition
            if isinstance(nodeset, dict) and "UAVariables" in nodeset:
                node_def = nodeset["UAVariables"][i] if i < len(nodeset["UAVariables"]) else {}
            elif isinstance(nodeset, list):
                node_def = nodeset[i] if i < len(nodeset) else {}
            else:
                node_def = {}
            
            # Try to get path from multiple sources (in priority order)
            path_parts = None
            
            # 1. Check for explicit Path field (preferred)
            if "Path" in node_def:
                path_str = node_def["Path"]
                if isinstance(path_str, str) and path_str:
                    path_parts = path_str.split(".")
            
            # 2. Try NodeId string identifier (e.g., "ns=1;s=Machine.Tank.Temperature")
            if not path_parts:
                node_id = node_def.get("NodeId", "")
                if isinstance(node_id, str) and ";s=" in node_id:
                    id_part = node_id.split(";s=")[-1]
                    if "." in id_part:
                        path_parts = id_part.split(".")
                elif isinstance(node_id, dict):
                    id_val = node_id.get("Id", "")
                    if isinstance(id_val, str) and "." in id_val:
                        path_parts = id_val.split(".")
            
            # Build nested structure from path
            if path_parts and len(path_parts) > 1:
                nested = self._build_nested_dict(path_parts, value)
                data = self._merge_nested_dicts(data, nested)
                logger.debug(f"Added nested variable: {'.'.join(path_parts)} = {value}")
            else:
                # Fallback: use display name or browse name
                clean_name = browse_name.split(":")[-1] if ":" in browse_name else browse_name
                if display_name and display_name != browse_name:
                    clean_name = display_name
                data[clean_name] = value
                logger.debug(f"Added flat variable: {clean_name} = {value}")
        
        return {"tsp": tsp, "data": data}

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
            logger.warning("No leaf nodes found in schema")
            return {"tsp": tsp, "data": populated_schema} # Return schema with unresolved values if no nodes found

        # Prepare for bulk reading
        nodes_to_read = []
        node_id_to_schema_info = {}

        for full_opcua_path_string, node_id, schema_parent_path, schema_key_for_variable, opcua_variable_name in leaf_nodes_info:
            nodes_to_read.append(self.client.get_node(node_id))
            # Store a reference back to the exact location in the populated_schema
            node_id_to_schema_info[str(node_id)] = (schema_parent_path, schema_key_for_variable, opcua_variable_name)

        if not nodes_to_read:
            logger.warning("No nodes to read after resolution")
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
            logger.info(f"Node: {child}")