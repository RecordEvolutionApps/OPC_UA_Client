import json
import os
from datetime import datetime
from asyncio import sleep
from asyncio.events import get_event_loop
from asyncua import Client
from ironflock import IronFlock
from flatTree import json_tree_to_table
from OPCUAClient import OPCUAClient

OPCUA_URL = os.environ.get("OPCUA_URL", "opc.tcp://localhost:4840/opcuaserver")
OPCUA_NAMESPACE = os.environ.get("OPCUA_NAMESPACE", "example:ironflock:com")
OPCUA_VARIABLES = os.environ.get("OPCUA_VARIABLES", '{"Tank": "Temperature"}')
PUBLISH_INTERVAL = int(os.environ.get("PUBLISH_INTERVAL", 3))

rw = IronFlock()

async def main():
    opcua_client = OPCUAClient(OPCUA_URL, OPCUA_NAMESPACE)
    await opcua_client.connect()
    await opcua_client.print_all_nodes()

    while True:
        # try:
        data = await opcua_client.read_from_schema(json.loads(OPCUA_VARIABLES))
        print(f"Value read {data}")
        for item in data:
            await rw.publish_to_table('opcuadata', item)
        # except Exception as e:
        #     print("could not get variable")
        #     print(e)

        await sleep(PUBLISH_INTERVAL)


if __name__ == "__main__":
    # run the main coroutine
    get_event_loop().create_task(main())
    # run the ironflock component
    rw.run()