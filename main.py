import json
import os
import logging
import signal
from asyncio import sleep
from ironflock import IronFlock
from OPCUAClient import OPCUAClient
from datetime import datetime
from flatTree import json_tree_to_table

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clean_multiline_env_var(env_value):
    """
    Clean multiline YAML strings that come from environment variables.
    Handles escaped newlines (\n) and actual newlines, strips extra whitespace.
    """
    if not env_value:
        return env_value
    
    # Replace literal \n strings with actual newlines
    cleaned = env_value.replace('\\n', '\n')
    
    # Remove leading/trailing whitespace from each line
    lines = [line.strip() for line in cleaned.split('\n')]
    
    # Join back together, removing empty lines
    cleaned = ''.join(line for line in lines if line)
    
    return cleaned

DEVICE_KEY = os.environ["DEVICE_KEY"]
DEVICE_NAME = os.environ.get("DEVICE_NAME")
OPCUA_URL = os.environ.get("OPCUA_URL", "opc.tcp://localhost:4840/opcuaserver")
OPCUA_NAMESPACE = os.environ.get("OPCUA_NAMESPACE", "example:ironflock:com")
OPCUA_VARIABLES = os.environ.get("OPCUA_VARIABLES", '{"Tank": "Temperature"}')
PUBLISH_INTERVAL = int(os.environ.get("PUBLISH_INTERVAL", 3))
MACHINE_NAME = os.environ.get("MACHINE_NAME")

# Global state for graceful shutdown
shutdown_requested = False
opcua_client_instance = None

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_requested = True

async def register_device():
        logger.info("Storing Device info...")
        await ironflock.publish_to_table(
            "devices",
            {
                "tsp": datetime.now().astimezone().isoformat(),
                "url": f"https://{DEVICE_KEY}-opc_ua_client-1881.app.ironflock.com",
                "machine_name": MACHINE_NAME or DEVICE_NAME,
                "deleted": False
            },
        )
        logger.info("Device Info registered")

async def register_measures(tab):
        logger.info("Storing Measure info...")
        for row in tab:
            await ironflock.publish_to_table(
                "opcua_flat_measures",
                {
                    "tsp": datetime.now().astimezone().isoformat(),
                    "measure_name": row["variable"],
                    "machine_name": MACHINE_NAME,
                    "deleted": False
                },
            )
        logger.info("Measure Info registered")


async def main():
    global opcua_client_instance, shutdown_requested
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    opcua_client = OPCUAClient(OPCUA_URL, OPCUA_NAMESPACE)
    opcua_client_instance = opcua_client
    
    try:
        logger.info(f"Connecting to OPC UA server at {OPCUA_URL}...")
        await opcua_client.connect()
        logger.info("Connected to OPC UA server")
        await opcua_client.print_all_nodes()

        await register_device()

        first_response = True
        
        # Parse OPCUA_VARIABLES - could be NodeSet or legacy schema
        # Clean multiline YAML input (handles \n escapes and whitespace)
        cleaned_variables = clean_multiline_env_var(OPCUA_VARIABLES)
        logger.debug(f"Cleaned OPCUA_VARIABLES: {cleaned_variables}")
        
        try:
            variables_config = json.loads(cleaned_variables)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OPCUA_VARIABLES as JSON: {e}")
            logger.error(f"Raw value: {OPCUA_VARIABLES}")
            logger.error(f"Cleaned value: {cleaned_variables}")
            raise
        
        # Detect if it's a NodeSet structure (list or dict with NodeClass)
        is_nodeset = False
        if isinstance(variables_config, list):
            is_nodeset = True
        elif isinstance(variables_config, dict) and "NodeClass" in variables_config:
            is_nodeset = True
            variables_config = [variables_config]  # Convert single node to list
        
        logger.info(f"Using {'NodeSet' if is_nodeset else 'legacy schema'} format for variable configuration")
        
        while not shutdown_requested:
            try:
                # Read data based on format
                if is_nodeset:
                    data = await opcua_client.read_from_nodeset(variables_config)
                else:
                    data = await opcua_client.read_from_schema(variables_config)
                
                logger.debug(f"Value read: {data}")
                flattab = json_tree_to_table(data)

                await ironflock.publish_to_table('opcuadata', OPCUA_NAMESPACE, MACHINE_NAME, data)

                if first_response:
                    first_response = False
                    await register_measures(flattab)
                
                for row in flattab:
                    logger.debug(f"Publishing row: {row}")
                    await ironflock.publish_to_table('flatopcuadata', OPCUA_NAMESPACE, MACHINE_NAME, row)

            except Exception as e:
                logger.error(f"Error reading/publishing OPC UA variables: {e}", exc_info=True)
                await sleep(5)  # Backoff on error
                continue

            await sleep(PUBLISH_INTERVAL)
    
    except Exception as e:
        logger.error(f"Fatal error in main loop: {e}", exc_info=True)
        raise
    finally:
        logger.info("Disconnecting from OPC UA server...")
        try:
            await opcua_client.disconnect()
            logger.info("Disconnected successfully")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}", exc_info=True)

if __name__ == "__main__":
    ironflock = IronFlock(mainFunc=main)
    ironflock.run()