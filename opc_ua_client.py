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
SERVER_ADDRESS      = os.environ.get('SERVER_ADDRESS', "opc.tcp://0.0.0.0:4840/freeopcua/server/")
LISTEN_NAMESPACE    = os.environ.get("LISTEN_NAMESPACE", "OPCUA_SERVER_Reswarm")
ENABLE_ENCRYPTION   = os.environ.get('ENABLE_ENCRYPTION', True)
READ_OBJECTS       = os.environ.get("READ_OBJECTS", ["ObjectOne"])
READ_VARIABLES     = os.environ.get("READ_VARIABLES", [["Timestamp", "Devicename"]])
WRITE_TO_PIPE       = os.environ.get('WRITE_TO_PIPE', ['opc_ua_client_1'])
FREQ_DATA_LOG       = 1
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
                    except UaError:
                        print("WARNING:__WrongNode__:no value found for object node: ", READ_OBJECTS[index], " and variable node: ",  
                        var_add[index_var])
                        print("SLEEP:__Wait__:wait 10 seconds for data")
                        time.sleep(10)
                        try:
                            value_server = root.get_child([main_object, sub_object, var_read]).get_value()
                            toWrite[var_add[index_var]] = value_server
                        except UaError:
                            print("WARNING:__NoValue__:no value found for object node: ", READ_OBJECTS[index], " and variable node: ",  
                            var_add[index_var])
                            print("closing the object node: ", READ_OBJECTS[index], " and variable node: ",  var_add[index_var])
                            close_node.append(name_to_append)
    except KeyboardInterrupt:
        client.disconnect()
    return toWrite

if __name__== "__main__":
    all_node = []
    close_node = []

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
            os.mkfifo(path_pipe)
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


init_node(idx_namespace)
stop_program = False
while not stop_program:
    data_received = start_client(idx_namespace)
    print(data_received)
    write_to_pipe(data_received, globals()[WRITE_TO_PIPE[0]])
    if set(all_node) == set(close_node):
        stop_program = True
        logger.info("all nodes are closed. Closing the OPC UA Client")
    time.sleep(FREQ_DATA_LOG)


    




