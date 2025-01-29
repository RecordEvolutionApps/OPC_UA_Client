import json
import os
from datetime import datetime
from asyncio import sleep
from asyncio.events import get_event_loop
from asyncua import Client
from ironflock import IronFlock

OPCUA_URL = os.environ.get("OPCUA_URL", "opc.tcp://localhost:4840/opcuaserver")
OPCUA_NAMESPACE = os.environ.get("OPCUA_NAMESPACE", "example:ironflock:com")
OPCUA_VARIABLES = os.environ.get("OPCUA_VARIABLES", '{"Tank": "Temperature"}')
PUBLISH_INTERVAL = int(os.environ.get("PUBLISH_INTERVAL", 3))

rw = IronFlock()

class OpcuaClient:
    _client = None
    _nsidx = None

    def __init__(self, url: str, namespace: str) -> None:
        self._url = url
        self._namespace = namespace

    @staticmethod
    async def _read_variables(client, nsidx, obj_vars_dict):
        result = dict()
        for object_name, variable_names in obj_vars_dict.items():
            if type(variable_names) is list:
                tmp = []
                for vname in variable_names:
                    node = await client.nodes.root.get_child(
                        [
                            "0:Objects",
                            f"{nsidx}:{object_name}",
                            f"{nsidx}:{vname}",
                        ]
                    )
                    v = await node.read_value()
                    tmp.append(v)

                result[object_name] = tmp

            else:
                node = await client.nodes.root.get_child(
                    [
                        "0:Objects",
                        f"{nsidx}:{object_name}",
                        f"{nsidx}:{variable_names}",
                    ]
                )
                v = await node.read_value()
                result[object_name] = v

        return result

    async def read_variables(self, obj_vars_dict):
        # create & connect client
        if self._client is None:
            self._client = Client(url=self._url)
            try:
                await self._client.connect()

                # Find the namespace index
                self._nsidx = await self._client.get_namespace_index(self._namespace)
                print(f"Namespace Index for '{self._namespace}': {self._nsidx}")

            except Exception as e:
                await self._client.disconnect()
                self._client = None
                raise e

        # read variable
        try:
            values = await self._read_variables(
                self._client, self._nsidx, obj_vars_dict
            )
            return values
        except Exception as e:
            await self._client.disconnect()
            self._client = None
            raise e

def resultToPayload(data):
    tsp = datetime.now().astimezone().isoformat()
    result = [
        {"tsp": tsp, "variable": key, "value": val}
        for key, values in data.items()
        for val in (values if isinstance(values, list) else [values])
    ]
    return result


async def main():
    opcua_client = OpcuaClient(OPCUA_URL, OPCUA_NAMESPACE)

    while True:
        try:
            data = await opcua_client.read_variables(json.loads(OPCUA_VARIABLES))
            print(f"Value read {data}")
            payload = resultToPayload(data)
            print("publish payload", payload)
            for item in payload:
                await rw.publish_to_table('opcuadata', item)
        except Exception as e:
            print("could not get variable")
            print(e)

        await sleep(PUBLISH_INTERVAL)


if __name__ == "__main__":
    # run the main coroutine
    get_event_loop().create_task(main())
    # run the ironflock component
    rw.run()