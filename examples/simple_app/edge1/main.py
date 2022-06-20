# coding:utf-8
from ecci_sdk import Client
import os
import threading
import time
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def transfer():
    while True:
        if len(ecci_client.get_sub_put_file_dict())>0 :
            (key,value)=ecci_client.get_sub_put_file_dict().popitem()
            ecci_client.transfer(key,'edge2')

def puturl():
    for i in range(3):
        ecci_client.putHandler(f'testfile{str(i)}','edge2',contents=f"This is a sentence named as testFile{str(i)} to show the file transfer that will be sent as a file")

if __name__ == "__main__":
    ecci_client = Client()
    # Initialize ecci sdk and connect to the broker in edge-cloud
    mqtt_thread = threading.Thread(target=ecci_client.initialize)
    mqtt_thread.start()
    #ecci_client.initialize()
    # Enter program block until 'start' control information is received
    ecci_client.wait_for_ready()
    logger.debug("start")
    # Collect the current time and send to edge2
    for i in range(10):
        print('start pub time--------------')
        # Define the message type as 'data'
        payload = {"type":"data","contents":{"start_time":time.time()}}
        # Send a message to the 'edge2 defined in the logical topology
        ecci_client.publish(payload, "edge2")

    while True:        
        # Message queues for 'cmd' type
        cmd_msg_queue = ecci_client.get_sub_cmd_payload_queue()
        if not cmd_msg_queue.empty():
            # The 'contents' section of the cmd message
            cmd_msg = cmd_msg_queue.get()
            # Message sender
            cmd_sender = ecci_client.get_sub_cmd_sender_queue().get()
            if cmd_msg['cmd'] == 'file':
                print('start pub file--------------')
                # Tell the target container GetUrl
                thread_transfer = threading.Thread(target=transfer)
                # Get PutUrl and upload files to minio
                thread_puturl = threading.Thread(target=puturl)
                thread_transfer.start()
                thread_puturl.start()
                thread_puturl.join()
                thread_transfer.join()

    
