# coding:utf-8
from ecci_sdk import Client
import os
import threading
import time
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def receive_mqtt_msg():
    msg_num = 0
    while True:        
        # Message queues for 'data' type
        data_msg_queue = ecci_client.get_sub_data_payload_queue()
        if not data_msg_queue.empty():
            # The 'contents' section of the data message
            data_msg = data_msg_queue.get()
            msg_num = msg_num + 1
            # Message sender
            data_sender = ecci_client.get_sub_data_sender_queue().get()
            # Message start time and transfer time
            start_time = data_msg['start_time']
            transfer_time = data_msg['transfer_time']
            # Calculate and print the delay
            print(f'edge1——edge2:{str(transfer_time-start_time)}\nedge2——cloud:{str(time.time()-transfer_time)}')
        if msg_num == 10:
            break
    # Notifies the 'edge1' container to send file
    payload = {"type":"cmd","contents":{"cmd":"file"}}
    print(payload)
    ecci_client.publish(payload, "edge1")

def receive_file():
    while True:
        if len(ecci_client.get_sub_get_file_dict().keys())>0:
            print('receive file from edge2')
            (key,value)=ecci_client.get_sub_get_file_dict().popitem()
            ecci_client.download_file(r'./testFile.txt', value)
            break
    time.sleep(1)
    with open(r'./testFile.txt', 'r') as f:
        print(f.read())

if __name__ == "__main__":
    ecci_client = Client()
    # Initialize ecci sdk and connect to the broker in central-cloud
    # ecci_client.initialize()
    mqtt_thread = threading.Thread(target=ecci_client.initialize)
    mqtt_thread.start()
    # Wait for the container on the side to be ready
    # time.sleep(10)
    ecci_client.wait_for_ready()
    # Notifies the 'edge1' container to start
    # payload = {"type":"cmd","contents":{"cmd":"start"}}
    # ecci_client.publish(payload, "edge1")
    # Receive mqtt msg
    print('start --------')
    thread_mqtt = threading.Thread(target=receive_mqtt_msg)
    # Receive file
    thread_file = threading.Thread(target=receive_file)
    thread_mqtt.start()
    thread_file.start()
    thread_file.join()
    thread_mqtt.join()



