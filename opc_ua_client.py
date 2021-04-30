from opcua import ua, Client
import opcua.ua.uaerrors
from datetime import datetime
import logging
import time
import json
import csv
import sys
import os
import concurrent.futures

print("********************Get Environment Variables********************")
SERVER_ADDRESS         = os.environ.get('SERVER_ADDRESS', "opc.tcp://127.0.0.1:12345")
LISTEN_NAMESPACE       = os.environ.get('LISTEN_NAMESPACE', "OPUA_test_server")
ENABLE_ENCRYPTION      = os.environ.get('ENABLE_ENCRYPTION', False)
READ_OBJECTS           = os.environ.get('READ_OBJECTS', ["Object_Node_1", "Object_Node_2"])
READ_VARIABLES        = os.environ.get('READ_VARIABLES',["Variable_1", "Variable_2"])
WRITE_TO_PIPE         = os.environ.get('WRITE_TO_PIPE', ['opc_ua_client_1', 'opc_ua_client_2'])
FREQ_DATA_LOG         = 1
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

    SOME UPDATED HERE ==========!@!@!@!@!!@@ ===========
        
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
		#var_add = READ_VARIABLES[index]
		var_add = READ_VARIABLES
		for index_var in range(0, len(var_add)):
			name_to_append = "0:Objects" + str(name_space) + ":" + READ_OBJECTS[index] + str(name_space) + ":" + var_add[index_var]
			all_node.append(name_to_append)

def receive_data(name_space,idx):
	global stop_worker
	toWrite = {}
	try:
		var_add = READ_VARIABLES
		main_object = "0:Objects"
		sub_object = str(name_space) + ":" + READ_OBJECTS[idx]
		status_node = str(name_space) + ":" + 'Status'
		status=root.get_child([main_object, sub_object, status_node]).get_value()
		print('Status:', idx, ', ', status)
		if status == 'Sent':
			root.get_child([main_object, sub_object, status_node]).set_value('Reading')
			for index_var in range(0, len(var_add)):
				var_read = str(name_space) + ":" + var_add[index_var]
				name_to_append = main_object + sub_object + var_read
				#if name_to_append not in close_node:
				if stop_worker[idx] is not True:
					try:
						value_server = root.get_child([main_object, sub_object, var_read]).get_value()
						print([main_object, sub_object, var_read])
						print("value_server", idx, ', ', value_server)
						toWrite[var_add[index_var]] = value_server
						#print('Var Property: ', root.get_child([main_object, sub_object, var_read]).get_parent().get_properties()[index_var].get_value())
						#print('Node: ', root.get_child([main_object, sub_object, var_read]).get_parent().get_properties()[index_var])
					except oSError as e:
						if e.errno == 32:
							print('Wrong node')
							time.sleep(10)
						else:
							print('Connection refuse')
							try:
								value_server = root.get_child([main_object, sub_object, var_read]).get_value()
								toWrite[var_add[index_var]] = value_server
							except oSError as e:
								if e.errno == 32:
									print("closing the object node")
									#close_node.append(name_to_append)
									stop_worker[idx] = True
								else:
									print("Connection Refuse")
			root.get_child([main_object, sub_object, status_node]).set_value('Read')
	except KeyboardInterrupt:
		client.disconnect()
	print('to write: ', idx, ', ', toWrite)
	return toWrite

def start_worker(idx):
	global stop_worker
	while not stop_worker[idx]:
		try:
			data_received[idx] = receive_data(idx_namespace, idx)
			print("data received:", idx, ', ', data_received[idx])
			if update_status[idx] == data_received[idx] or data_received[idx]=={}: #NEW!!!
			#if data_received[idx] == {}:
				print('node value not updated') #NEW!!!
			else:                               #NEW!!!
				write_to_pipe(data_received[idx],globals()[WRITE_TO_PIPE[idx]]) #NEW!!!
			#if set(all_node) == set(close_node):
			if stop_worker[idx] == True:
				#stop_worker = True
				os.close(globals()[WRITE_TO_PIPE[idx]])
				#client.disconnect()
			update_status[idx] = data_received[idx]
			time.sleep(FREQ_DATA_LOG)
		except KeyboardInterrupt:
			os.close(globals()[WRITE_TO_PIPE[idx]])
			client.disconnect()
			sys.exit(0)

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

    all_node = []
    print("********************Create Output Pipe********************")
    for pipes in WRITE_TO_PIPE:
        path_pipe = '/shared' + os.path.join('/', pipes)
        try:
            os.mkfifo(path_pipe)
        except FileNotFoundError as e:
            if os.path.exists(path_pipe):
                print("ERROR:__PathNotExist__:path does not exist")
                sys.exit(0)
        except OSError as e:
            print("INFO:__CreatePipe__:pipe already exist")
            pass

        try:
            #globals()[WRITE_TO_PIPE] = os.open(path_pipe, os.O_RDWR)
            globals()[pipes] = os.open(path_pipe, os.O_RDWR)
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
        if ENABLE_ENCRYPTION:
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
    objects= client.get_objects_node()
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
    update_status = [None] * len(READ_OBJECTS)
    data_received = [None] * len(READ_OBJECTS)
    stop_worker = [False] * len(READ_OBJECTS)
    idx = [r for r in range(0,len(READ_OBJECTS))]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(start_worker, idx)