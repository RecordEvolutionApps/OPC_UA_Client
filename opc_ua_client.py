from opcua import ua, uamethod, Client
from datetime import datetime
import logging
import time
import os

# Get environment variables
print("********************Get Environment Variables********************")
SERVER_ADDRESS      = os.environ.get('SERVER_ADDRESS', "opc.tcp://0.0.0.0:4840/freeopcua/server/")
SERVER_URL_TOPIC    = os.environ.get("SERVER_URL_TOPIC", "OPCUA_SERVER_Reswarm")
ENABLE_ENCRYPTION   = os.environ.get('ENABLE_ENCRYPTION', True)
READ_NODE_S         = os.environ.get("READ_NODE_S", ["Node1"])
READ_VARIABLE_S     = os.environ.get("READ_VARIABLE_S", [["Timestamp", "Devicename"], ["String1", "String2"]])
READ_OBJECT_S       = os.environ.get("READ_OBJECT_S", ["ObjectOne", "ObjectTwo"])
FREQ_DATA_LOG       = float(os.environ.get('FREQ_DATA_LOG', '2'))
print('User specified values are set')

# Initiate logger
print("********************Initiating Logger********************")
logging.basicConfig(level=logging.WARN)
print("Logging initiated")

# Setup client
print("********************Set Endpoint of OPC UA Client********************")
try:
    client = Client(SERVER_ADDRESS)
    print("Endpoint for OPC UA client is set to: ", SERVER_ADDRESS)
except Exception as e:
    print("Error while setting up endpoint for OPC UA client! ", e)
    os.system('exit')

print("********************Setting Encryption********************")
if ENABLE_ENCRYPTION:
    client.set_security_string("Basic256Sha256,SignAndEncrypt,certificate-example.der,private-key-example.pem")
    client.secure_channel_timeout = 10000
    client.session_timeout = 10000
    print("Client Encryption enabled")
else:
    print("Client Encryption disabled")

print("********************Initialize OPC UA Server********************")
# Connect the client
try:
    client.connect()
except Exception as e:
    print("Error while connecting the client ", e)
    os.system('exit')

# Load definition of server specific structures/extension objects
client.load_type_definitions

# Client has a few methods to get proxy to UA nodes that should always be in address space such as Root or Objects
root = client.get_root_node()
print("Root node is: ", root)
objects = client.get_objects_node()
print("Objects node is: ", objects)

# Node objects have methods to read and write node attributes as well as browse or populate address space
print("Children of root are: ", root.get_children())

print("********************Get Namespace********************")
# gettting our namespace idx
try:
    idx_namespace = client.get_namespace_index(SERVER_URL_TOPIC)
    children_root = root.get_children()
    print("Registered namespace: ", SERVER_URL_TOPIC)
except Exception as e:
    print("Error getting namespace! ", e)

dicts = {}
try: 
    while True:
        for ichild in range(0, len(READ_NODE_S)):
            dicts["node"] = READ_NODE_S[ichild]
            for index in range(0, len(READ_OBJECT_S)):
                var_add = READ_VARIABLE_S[index]
                dicts["object"] = READ_OBJECT_S[index]
                for index_var in range(0, len(var_add)):
                    main_object = "0:Objects"
                    sub_object = str(idx_namespace) + ":" + READ_OBJECT_S[index]
                    var_read = str(idx_namespace) + ":" + var_add[index_var]
                    value_server = root.get_child([main_object, sub_object, var_read]).get_value()
                    dicts["variable"] = var_add[index_var]
                    dicts["value"] = value_server
                    print(dicts)
        dicts = {}
        time.sleep(FREQ_DATA_LOG)

except KeyboardInterrupt:
    client.disconnect()

