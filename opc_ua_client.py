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
DATA_SUBFOLDER      = '/shared' + os.path.join('/', os.environ.get('DATA_SUBFOLDER', 'opc_ua_client'))
SERVER_ADDRESS      = os.environ.get('SERVER_ADDRESS', "opc.tcp://0.0.0.0:4840/freeopcua/server/")
LISTEN_NAMESPACE    = os.environ.get("LISTEN_NAMESPACE", "OPCUA_SERVER_Reswarm")
ENABLE_ENCRYPTION   = os.environ.get('ENABLE_ENCRYPTION', True)
READ_NODE_S         = os.environ.get("READ_NODE_S", ["Node1"])
READ_VARIABLE_S     = os.environ.get("READ_VARIABLE_S", [["Timestamp", "Devicename"], ["Temperature", "Volt"]])
READ_OBJECT_S       = os.environ.get("READ_OBJECT_S", ["ObjectOne", "ObjectTwo"])
TOPIC_PREFIX        = os.environ.get('TOPIC_PREFIX', 'reswarm.opc_ua_client')
WRITE_FILE          = os.environ.get('WRITE_FILE', 'ON')
PUBLISH_DATA        = os.environ.get('PUBLISH_DATA', 'ON')
FREQ_DATA_LOG       = float(1/os.environ.get('FREQ_DATA_LOG', 2.0))
MAX_ROWS_PER_FILE   = float(os.environ.get('MAX_ROWS_PER_FILE', 50))
MAX_TIME_PER_FILE   = float(os.environ.get('MAX_TIME_PER_FILE', 30))
print('User specified values are set')


print("********************Initializing WAMP Agent********************")
"""
    WAMP router functions demonstrated:
        onJoin
        on_leave
        on_disconnect
        on_connectfailure

    Purpose:
        Create a Autobahn component using the Twisted approach for an IoT connector in Repods

    Description:
        A connection to WAMP router is established and the fetched data from OPC UA server
        is published to the router.
        
"""
comp = Component(
    transports={
                "type": "websocket",
                "url": "ws://cb.reswarm.io:8088",
                "max_retries": -1,
                "max_retry_delay": 2,
                "initial_retry_delay": 0.5,
                # "autoping_interval": 2,
                # "autoping_timeout": 4
                },
    realm=u"userapps",
    authentication={
        u"wampcra": {
            u'authid': os.environ['DEVICE_SERIAL_NUMBER'],
            u'secret': os.environ['DEVICE_SERIAL_NUMBER']
        }
    },
)

@comp.on_join
def onJoin(session, details):
    print("Session: {} - Details: {}".format(session, details))
    
    @inlineCallbacks
    def publish_opc_client():
        #print('size' + str(pub_buffer.qsize()))
        while not pub_buffer.empty():
            data = pub_buffer.get()
            #print('publish data' + str(data))
            if data and PUBLISH_DATA == 'ON':
                try:
                    yield session.publish(TOPIC_PREFIX + '.' + os.environ['DEVICE_SERIAL_NUMBER'], data, options=PublishOptions(acknowledge=True)) # for datapods to listen on
                except:
                    print('Failed to publish data')
                    pub_buffer.put(data)
            
    print('starting pub loop')
    LoopingCall(publish_opc_client).start(1.0/FREQ_DATA_LOG)

@comp.on_leave
def onLeave(session, details):
    print('onLeave...')
    session.disconnect()

@comp.on_disconnect
def onDisconnect(session, was_clean):
    print('onDisconnect...')

@comp.on_connectfailure
def onConnectfailure(session, was_clean):
    print('onConnectfailure...')
print("WAMP agent initialized")

"""
    Write csv file functions demonstrated:
        write_to_file
        init_file

    Purpose:
        Initiate and write data to the csv file

"""

def write_to_file():
    """
    Write data to the csv file
    """
    
    time_write = time.time() + MAX_TIME_PER_FILE
    while not write_buffer.empty():
        data = write_buffer.get()
        if not data: return
        
        global writer
        global file_size_counter
        global time_flush
        global file_name
        global file_out

        writer.writerow(data)
        file_size_counter += 1

        # Count the iterations
        if(time.time() >= time_flush):
            print('flushing to disk')
            file_out.flush()
            time_flush = time.time() + 5

        #check the size of output file
        if file_size_counter >= MAX_ROWS_PER_FILE or time.time() >= time_write:
            print('File '+ os.path.basename(file_name) + ' max row number reached ' + str(MAX_ROWS_PER_FILE) + '. Starting a new file now.')
            time_write = time.time() + MAX_TIME_PER_FILE
            file_size_counter = 0
            file_out.close()
            init_file()

            
def init_file():
    """
    Initiate the csv file
    """

    global writer
    global file_size_counter
    global time_flush
    global file_name
    global file_out
    global DATA_SUBFOLDER

    time_flush = time.time() + 5
    file_size_counter = 0
    if file_out:
        os.rename(file_name, '.'.join(file_name.split('.')[:-1]) + '.csv')
        file_out.close()
    file_name = os.path.join(DATA_SUBFOLDER, 'OPC_UA_CLIENT_' + str(datetime.now().strftime('%Y_%m_%d_%H_%M_%S')) + '.csv')
    file_out = open(file_name, 'w')
    writer=csv.writer(file_out) 
    writer.writerow(['Node', 'Object', 'Variable', 'Value'])

"""
    OPC UA Client functions demonstrated:
        startClient

    Purpose:
        The function/example function fetch data from a OPC UA Server. 

    Description:
        These functions demonstrate the possibility of fetching sensor/controller/device data
        from a OPC UA server.
        
"""

def startClient():
    toPublish = []
    try: 
        # loop over nodes
        for ichild in range(0, len(READ_NODE_S)):
            toPublish.append(READ_NODE_S[ichild])

            # loop over objects
            for index in range(0, len(READ_OBJECT_S)):
                var_add = READ_VARIABLE_S[index]
                toPublish.append(READ_OBJECT_S[index])

                # loop over variables
                for index_var in range(0, len(var_add)):
                    main_object = "0:Objects"
                    sub_object = str(idx_namespace) + ":" + READ_OBJECT_S[index]
                    var_read = str(idx_namespace) + ":" + var_add[index_var]
                    try:
                        value_server = root.get_child([main_object, sub_object, var_read]).get_value()
                    except Exception as e:
                        print("Error reading value for Object: ", READ_OBJECT_S[index], " and Variable: ",  
                        var_add[index_var], "! Probably OPC UA server is not configure to send data for Object: ", 
                        READ_OBJECT_S[index], " and Variable: ", var_add[index_var])
                        os.system('exit')
                    toPublish.append(var_add[index_var])
                    toPublish.append(value_server)

                    # publish the data to WAMP router
                    if PUBLISH_DATA == 'ON':pub_buffer.put(toPublish)
                    if WRITE_FILE   == 'ON':write_buffer.put(toPublish)
                    if pub_buffer.qsize() > 500000: pub_buffer.get()
                    if write_buffer.qsize() > 500000: write_buffer.get()
    except KeyboardInterrupt:
        client.disconnect()

if __name__== "__main__":

    # Create output directory 
    print("********************Create Output File********************")
    os.makedirs(DATA_SUBFOLDER, exist_ok=True)
    file_name  = DATA_SUBFOLDER + '/' + 'OPC_UA_CLIENT_' + str(datetime.now().strftime('%Y_%m_%d_%H_%M_%S')) + '.csv'
    print("Output csv file is created", file_name)

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
        idx_namespace = client.get_namespace_index(LISTEN_NAMESPACE)
        children_root = root.get_children()
        print("Registered namespace: ", LISTEN_NAMESPACE)
    except Exception as e:
        print("Error getting namespace! ", e)

    
    # Initiate csv file
    init_file()

    LoopingCall(startClient).start(1.0/FREQ_DATA_LOG)

    # Write to csv file
    if WRITE_FILE == 'ON':
        LoopingCall(write_to_file).start(1.0/FREQ_DATA_LOG)

    # Publish the data to the WAMP agent
    if PUBLISH_DATA == 'ON':
        comp.start()

    from twisted.internet import reactor
    reactor.run()




