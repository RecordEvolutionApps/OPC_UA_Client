from autobahn.twisted.component import Component
from autobahn.twisted.util import sleep
from autobahn.wamp.types import PublishOptions
from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks
from opcua import ua, Client
from datetime import datetime
from queue import Queue
import subprocess
import logging
import time
import csv
import sys
import os

# Declare global variables
global headers
global writer
global file_size_counter
global time_flush
global file_name
global file_out

# Initialiazation of Queue
file_out     = None
write_buffer = Queue()
pub_buffer   = Queue()

# Get environment variables
print("********************Get Environment Variables********************")
SERVER_ADDRESS      = os.environ.get('SERVER_ADDRESS', "opc.tcp://0.0.0.0:4840/freeopcua/server/")
LISTEN_NAMESPACE    = os.environ.get("LISTEN_NAMESPACE", "OPCUA_SERVER_Reswarm")
ENABLE_ENCRYPTION   = os.environ.get('ENABLE_ENCRYPTION', True)
READ_OBJECTS       = os.environ.get("READ_OBJECTS", ["ObjectOne", "ObjectTwo"])
READ_VARIABLES     = os.environ.get("READ_VARIABLES", [["Timestamp", "Devicename"], ["Temperature", "Volt"]])
WRITE_TO_PIPE       = os.environ.get('WRITE_TO_PIPE', ['opc_ua_client_1', 'opc_ua_client_2'])
FREQ_DATA_LOG       = float(1/os.environ.get('FREQ_DATA_LOG', 2.0))

print('User specified values are set')

"""
    OPC UA Client functions demonstrated:
        write_to_pipe
        startClient

    Purpose:
        The function/example function fetch data from a OPC UA Server. 

    Description:
        These functions demonstrate the possibility of fetching sensor/controller/device data
        from a OPC UA server.
        
"""

def write_to_pipe(data_in, output_pipe):
    if type(data_in) is dict:
        data_out = json.dumps(data_in).encode('utf-8')
    elif type(data) is str:
        data_out = data_in.encode()
    else:
        data_out = str(data_in).encode()
    os.write(output_pipe, data_out)

def startClient(name_space):
    try: 
        # loop over objects
        for index in range(0, len(READ_OBJECTS)):
            var_add = READ_VARIABLES[index]
            # loop over variables
            for index_var in range(0, len(var_add)):
                main_object = "0:Objects"
                sub_object = str(name_space) + ":" + READ_OBJECTS[index]
                var_read = str(name_space) + ":" + var_add[index_var]
                try:
                    value_server = root.get_child([main_object, sub_object, var_read]).get_value()
                    print(value_server)
                except Exception as e:
                    print("Error reading value for Object: ", READ_OBJECTS[index], " and Variable: ",  
                    var_add[index_var], "! Probably OPC UA server is not configure to send data for Object: ", 
                    READ_OBJECTS[index], " and Variable: ", var_add[index_var])
    except KeyboardInterrupt:
        client.disconnect()

if __name__== "__main__":

    print("********************Initiating Logger********************")
try:
    logging.basicConfig(level=logging.WARN)
    logger = logging.getLogger(__name__)
    logger.info(" Logging initiated")
except AttributeError:
    logging.error(" Logger not initialized!")

    print("********************Create Output Pipe********************")
for pipe_make in WRITE_TO_PIPE:
    path_pipe = '/shared' + os.path.join('/', pipe_make)
    try:
        os.mkfifo(pipe_make)
        print("INFO:__CreatePipe__:pipe created")
    except FileNotFoundError as e:
        print("ERROR:__CreatePipe__:cannot create pipe!", e)
        if os.path.exists(path_pipe):
            print("ERROR:__PathNotExist__:path does not exist")
            sys.exit(0)
    except OSError as e:
        print("INFO:__CreatePipe__:pipe already exist")
        pass
    try:
        globals()[pipe_make] = os.open(pipe_make, os.O_RDWR)
        print("INFO:__OpenPipe__:output pipe opened ", pipe_make)
    except NameError:
        print("ERROR:__OpenPipe__:cannot open pipe: ", pipe_make)
        print("program terminated!")
        sys.exit(0)

    print("********************Initialize OPC UA Client********************")
try:
    client = Client(SERVER_ADDRESS)
    logger.info(' OPC UA Client Initialized: ' + SERVER_ADDRESS)
except Exception:
    logging.exception("Client not initialized!")
    sys.exit(0)

print("********************Setting Encryption********************")
try:
    if ENABLE_ENCRYPTION:
        client.set_security_string("Basic256Sha256,SignAndEncrypt,certificate-example.der,private-key-example.pem")
        client.secure_channel_timeout = 10000
        client.session_timeout        = 10000
        logger.info("Encryption is enabled")
    else:
        logger.info("Client Encryption disabled")
except Exception:
    logger.exception("Error Client cannot listent to OPC UA Server! Please make sure that the OPC UA Server is running at " + 
    SERVER_ADDRESS)
    sys.exit(0)

    print("********************Initialize OPC UA Server********************")
try:
    client.connect()
    logger.info("INFO:ClinetConnect:client connected to server at " + SERVER_ADDRESS)
except Exception:
    logger.exception("client cannot connect to server at " + SERVER_ADDRESS)
    sys.exit(0)

    # Load definition of server specific structures/extension objects
client.load_type_definitions

# Client has a few methods to get proxy to UA nodes that should always be in address space such as Root or Objects
root = client.get_root_node()
logger.info("Root node is: ", root)
objects = client.get_objects_node()
logger.info("Objects node is: ", objects)

    # Node objects have methods to read and write node attributes as well as browse or populate address space
    logger.info("Children of root are: ", root.get_children())

    print("********************Get Namespace********************")
    # gettting our namespace idx
try:
    idx_namespace = client.get_namespace_index(LISTEN_NAMESPACE)
    children_root = root.get_children()
    logger.info("Registered namespace: ", LISTEN_NAMESPACE)
except Exception:
    logger.exception("cannot get server namespace!")

while True:
    startClient(idx_namespace)
    time.sleep(1)


    




