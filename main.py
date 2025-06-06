import json
import os
from asyncio import sleep
from asyncio.events import get_event_loop
from ironflock import IronFlock
from OPCUAClient import OPCUAClient

OPCUA_URL = os.environ.get("OPCUA_URL", "opc.tcp://localhost:4840/opcuaserver")
OPCUA_NAMESPACE = os.environ.get("OPCUA_NAMESPACE", "example:ironflock:com")
OPCUA_VARIABLES = os.environ.get("OPCUA_VARIABLES", '{"Tank": "Temperature"}')
PUBLISH_INTERVAL = int(os.environ.get("PUBLISH_INTERVAL", 3))


async def main():
    opcua_client = OPCUAClient(OPCUA_URL, OPCUA_NAMESPACE)
    await opcua_client.connect()
    await opcua_client.print_all_nodes()

    while True:
        # try:
        data = await opcua_client.read_from_schema(json.loads(OPCUA_VARIABLES))
        print(f"Value read {data}")
        await ironflock.publish_to_table('opcuadata', OPCUA_NAMESPACE, data)
        # except Exception as e:
        #     print("could not get variable")
        #     print(e)

        await sleep(PUBLISH_INTERVAL)

if __name__ == "__main__":
    ironflock = IronFlock(mainFunc=main)
    ironflock.run()