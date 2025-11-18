import json
import os
from asyncio import sleep
from asyncio.events import get_event_loop
from ironflock import IronFlock
from OPCUAClient import OPCUAClient
from datetime import datetime
from flatTree import json_tree_to_table

DEVICE_KEY = os.environ["DEVICE_KEY"]
DEVICE_NAMAE = os.environ.get("DEVICE_NAME")
OPCUA_URL = os.environ.get("OPCUA_URL", "opc.tcp://localhost:4840/opcuaserver")
OPCUA_NAMESPACE = os.environ.get("OPCUA_NAMESPACE", "example:ironflock:com")
OPCUA_VARIABLES = os.environ.get("OPCUA_VARIABLES", '{"Tank": "Temperature"}')
PUBLISH_INTERVAL = int(os.environ.get("PUBLISH_INTERVAL", 3))
MACHINE_NAME = os.environ.get("MACHINE_NAME")

async def register_device():
        print("########### Storing Device info ################")
        await ironflock.publish_to_table(
            "devices",
            {
                "tsp": datetime.now().astimezone().isoformat(),
                "url": f"https://{DEVICE_KEY}-opc_ua_client-1881.app.ironflock.com",
                "machine_name": MACHINE_NAME or DEVICE_NAMAE,
                "deleted": False
            },
        )
        print("Device Info registered")

async def register_measures(tab):
        print("########### Storing Measure info ################")
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
        print("Measure Info registered")


async def main():
    opcua_client = OPCUAClient(OPCUA_URL, OPCUA_NAMESPACE)
    await opcua_client.connect()
    await opcua_client.print_all_nodes()

    await register_device()

    first_response = True
    while True:
        # try:
        data = await opcua_client.read_from_schema(json.loads(OPCUA_VARIABLES))
        print(f"Value read {data}")
        flattab = json_tree_to_table(data)

        await ironflock.publish_to_table('opcuadata', OPCUA_NAMESPACE, MACHINE_NAME, data)

        if first_response:
            first_response = False
            await register_measures(flattab)
        
        for row in flattab:
            print(row)
            await ironflock.publish_to_table('flatopcuadata', OPCUA_NAMESPACE, MACHINE_NAME, row)


        # except Exception as e:
        #     print("could not get variable")
        #     print(e)

        await sleep(PUBLISH_INTERVAL)

if __name__ == "__main__":
    ironflock = IronFlock(mainFunc=main)
    ironflock.run()