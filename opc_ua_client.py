from opcua import ua, Client
import opcua.ua.uaerrors
from datetime import datetime
import logging
import time
import json
import csv
import sys
import os

print("********************Get Environment Variables********************")
SERVER_ADDRESS      = os.environ.get('SERVER_ADDRESS', "opc.tcp://0.0.0.0:4840/server/")
LISTEN_NAMESPACE    = os.environ.get("LISTEN_NAMESPACE", "OPCUA_SERVER_Reswarm")
ENABLE_ENCRYPTION   = os.environ.get('ENABLE_ENCRYPTION', 'true')
OBJ_VAR_NODES       = os.environ.get("OBJ_VAR_NODES")        
WRITE_TO_PIPE       = os.environ.get('WRITE_TO_PIPE')
FREQ_DATA_LOG       = 1        
env_var_json        = json.loads(OBJ_VAR_NODES)
READ_OBJECTS        = [*env_var_json.keys()]
READ_VARIABLES      = [*env_var_json.values()]
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
    #print("INFO:data received from OPC Server: " + str(data_out))
    os.write(output_pipe, data_out)

def init_node(name_space):
    global all_node
    for index in range(0, len(READ_OBJECTS)):
        var_add = READ_VARIABLES[index]
        for index_var in range(0, len(var_add)):
            name_to_append = "0:Objects" + str(name_space) + ":" + READ_OBJECTS[index] + str(name_space) + ":" + var_add[index_var]
            all_node.append(name_to_append)

def start_client(name_space):
    global close_node
    toWrite = {}
    try: 
        # loop over objects
        for index in range(0, len(READ_OBJECTS)):
            var_add = READ_VARIABLES[index]
            # loop over variables
            for index_var in range(0, len(var_add)):
                main_object = "0:Objects"
                sub_object = str(name_space) + ":" + READ_OBJECTS[index]
                var_read = str(name_space) + ":" + var_add[index_var]
                name_to_append = main_object + sub_object + var_read
                if name_to_append not in close_node:
                    try:
                        value_server = root.get_child([main_object, sub_object, var_read]).get_value()
                        toWrite[var_add[index_var]] = value_server
                    except OSError as e:
                        if e.errno == 32:
                            print("WARNING:__WrongNode__:no value found for object node: ", READ_OBJECTS[index], " and variable node: ",  
                            var_add[index_var])
                            print("SLEEP:__Wait__:wait 10 seconds for data")
                            time.sleep(10)
                        else:
                            print("ERROR:__ConnectionRefuse__:connection refused!")
                            try:
                                value_server = root.get_child([main_object, sub_object, var_read]).get_value()
                                toWrite[var_add[index_var]] = value_server
                            except OSError as e:
                                if e.errno == 32:
                                    print("closing the object node: ", READ_OBJECTS[index], " and variable node: ",  var_add[index_var])
                                    close_node.append(name_to_append)
                                else:
                                    print("ERROR:__ConnectionRefuse__:connection refused!")
    except KeyboardInterrupt:
        client.disconnect()
    return toWrite

if __name__== "__main__":
    all_node = []
    close_node = []

    print("********************Initiating Logger********************")
    try:
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        logger.info(" Logging initiated")
    except AttributeError:
        logging.error(" Logger not initialized!")

    print("********************Create Output Pipe********************")
    path_pipe = '/shared' + os.path.join('/', WRITE_TO_PIPE)
    try:
        os.mkfifo(path_pipe)
        print("INFO:__CreatePipe__:pipe created")
    except FileNotFoundError as e:
        print("ERROR:__CreatePipe__:cannot create pipe!", e)
        if os.path.exists(path_pipe):
            print("ERROR:__PathNotExist__:path does not exist ", path_pipe)
            sys.exit(0)
    except OSError as e:
        print("INFO:__CreatePipe__:pipe already exist")
        pass
    try:
        globals()[WRITE_TO_PIPE] = os.open(path_pipe, os.O_RDWR)
        print("INFO:__OpenPipe__:output pipe opened ", path_pipe)
    except NameError:
        print("ERROR:__OpenPipe__:cannot open pipe: ", path_pipe)
        print("program terminated!")
        sys.exit(0)

    print("********************Initialize OPC UA Client********************")
    try:
        client = Client(SERVER_ADDRESS)
        print('INFO:__OPCClient__:OPC UA Client Initialized: ' + SERVER_ADDRESS)
    except OSError as e:
        print("ERROR:__EndPoint__:Client not initialized! ", e)
        sys.exit(0)

    print("********************Setting Encryption********************")
    try:
        if ENABLE_ENCRYPTION == 'true':
            client.set_security_string("Basic256Sha256,SignAndEncrypt,certificate-example.der,private-key-example.pem")
            client.secure_channel_timeout = 10000
            client.session_timeout        = 10000
            print("INFO:__Encryption__:encryption is enabled")
        else:
            print("INFO:__Encryption__:client Encryption disabled")
    except OSError:
        print("ERROR:__ConnectionRefused__:client cannot listent to OPC UA Server!" + "\n" + 
        "Please make sure that the OPC UA Server is running at " + 
        SERVER_ADDRESS)
        sys.exit(0)

    print("********************Initialize OPC UA Server********************")
    try:
        client.connect()
        print("INFO:ClinetConnect:client connected to server at " + SERVER_ADDRESS)
    except OSError:
        print("ERROR:__ConnectionRefused__:client cannot connect to server" + "\n"
        "Please make sure that the OPC UA Server is running at " + 
        SERVER_ADDRESS)
        sys.exit(0)

    # Load definition of server specific structures/extension objects
    client.load_type_definitions

    # Client has a few methods to get proxy to UA nodes that should always be in address space such as Root or Objects
    root = client.get_root_node()
    print("INFO:__OPC UA Server__:root node is: ", root)
    objects = client.get_objects_node()
    print("INFO:__OPC UA Server__:objects node is: ", objects)

    # Node objects have methods to read and write node attributes as well as browse or populate address space
    print("INFO:__OPC UA Server__:children of root are: ", root.get_children())

    print("********************Get Namespace********************")
        # gettting our namespace idx
    try:
        idx_namespace = client.get_namespace_index(LISTEN_NAMESPACE)
        children_root = root.get_children()
        print("INFO:__OPC UA Server__:registered namespace: ", LISTEN_NAMESPACE)
    except ValueError:
        print("ERROR:__InvalidNameSpace__:invalid name space provided! ", LISTEN_NAMESPACE)
        sys.exit(0)

print("INFO:__GetData__:start reading server data")
init_node(idx_namespace)
stop_program = False
update_status = None
try:
    while not stop_program:
        data_received = start_client(idx_namespace)
        write_to_pipe(data_received, globals()[WRITE_TO_PIPE])
        if set(all_node) == set(close_node):
            stop_program = True
            print("INFO:__CloseNode__:all nodes are closed. Closing the OPC UA Client")
            os.close(globals()[WRITE_TO_PIPE])
            print("INFO:__ClosePipe__:closing output pipe " + WRITE_TO_PIPE)
            client.disconnect()
        if update_status == data_received:
            logger.warn('node value not updated')
        update_status = data_received
        time.sleep(FREQ_DATA_LOG)
except KeyboardInterrupt:
        os.close(globals()[WRITE_TO_PIPE])
        client.disconnect()


    




