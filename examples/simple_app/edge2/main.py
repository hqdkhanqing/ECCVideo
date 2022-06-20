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
            print('send file to cloud')
            (key,value)=ecci_client.get_sub_put_file_dict().popitem()
            ecci_client.transfer(key,'cloud')

def receive_mqtt_msg():
    while True:        
        # Message queues for 'data' type
        data_msg_queue = ecci_client.get_sub_data_payload_queue()
        if not data_msg_queue.empty():
            # The 'contents' section of the data message
            data_msg = data_msg_queue.get()
            print('receive msg from edge1')
            # Message sender
            data_sender = ecci_client.get_sub_data_sender_queue().get()
            # Message start time
            start_time = data_msg['start_time']
            # Define the message type as 'data'
            payload = {"type":"data","contents":{"start_time":start_time,"transfer_time":time.time()}}
            # Send a message to the 'cloud' defined in the logical topology
            ecci_client.publish(payload, "cloud")

def receive_file():
    content_num = 0
    while True:
        if len(ecci_client.get_sub_get_file_dict().keys())>0:
            (key,value)=ecci_client.get_sub_get_file_dict().popitem()
            content_num = content_num+1
            print('receive file from edge1')
            contents=ecci_client.download_contents(value)
            print(key)
            print(value)
            with open(r'./testFile.txt', 'a') as f:
                f.writelines(contents+'\n')
        if content_num == 3:
            break
    # Get PutUrl and upload files to minio
    ecci_client.putHandler('testfileall','cloud',filepath=r'./testFile.txt')

if __name__ == "__main__":
    ecci_client = Client()
    # Initialize ecci sdk and connect to the broker in edge-cloud
    mqtt_thread = threading.Thread(target=ecci_client.initialize)
    mqtt_thread.start()
    # Receive mqtt msg
    thread_mqtt = threading.Thread(target=receive_mqtt_msg)
    # Receive file
    thread_file = threading.Thread(target=receive_file)
    # Tell the target container GetUrl
    thread_transfer = threading.Thread(target=transfer)
    thread_mqtt.start()
    thread_transfer.start()
    thread_file.start()
    thread_file.join()
    thread_mqtt.join()
    thread_transfer.join()

