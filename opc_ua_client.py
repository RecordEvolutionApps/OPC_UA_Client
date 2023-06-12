import json
import os
from asyncio import sleep
from asyncio.events import get_event_loop
from asyncua import Client
from reswarm import Reswarm


OPCUA_URL = os.environ.get("OPCUA_URL", "opc.tcp://localhost:4840/freeopcua/server/")
OPCUA_NAMESPACE = os.environ.get("OPCUA_NAMESPACE", "http://examples.freeopcua.github.io")
OPCUA_VARIABLES = os.environ.get("OPCUA_VARIABLES", '{"MyObject": "MyVariable"}')
CB_TOPIC = os.environ.get("CB_TOPIC", "re.opcua.client")
PUBLISH_INTERVAL = int(os.environ.get("PUBLISH_INTERVAL", 3))



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


async def main():
    rw = Reswarm()

    opcua_client = OpcuaClient(OPCUA_URL, OPCUA_NAMESPACE)

    while True:
        try:
            value = await opcua_client.read_variables(json.loads(OPCUA_VARIABLES))
            print(f"Value read {value}")
            result = await rw.publish(CB_TOPIC, value)
            print(result)
        except Exception as e:
            print("could not get variable")
            print(e)

        await sleep(PUBLISH_INTERVAL)


if __name__ == "__main__":
    get_event_loop().run_until_complete(main())