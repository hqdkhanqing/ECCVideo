import paho.mqtt.client as mqtt
import threading
import os
import ast
import re
import _pickle as cPickle
from queue import Queue
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

BROKER_IP = os.getenv("ECCI_LOCAL_BROKER_IP", default="localhost")
BROKER_ID = os.getenv("ECCI_LOCAL_BROKER_ID")
BROKER_PORT = int(os.getenv("ECCI_LOCAL_BROKER_PORT", default=1883))
BROKER_USERNAME = os.getenv("ECCI_LOCAL_BROKER_USERNAME")
BROKER_PASSWORD = os.getenv("ECCI_LOCAL_BROKER_PASSWORD")

# BRIDGE_MOUNTPOINT = os.getenv("ECCI_BRIDGE_MOUNTPOINT",default="")
TOPIC_PREFIX = f"ECCI/{BROKER_ID}/+/plugin"

class MqttClient:

    def __init__(self):
        self._broker_ip = BROKER_IP
        self._broker_port = BROKER_PORT
        self._sub_file_sender_queue = Queue()
        self._sub_file_payload_queue = Queue()
        self._mqtt_client = None

    def get_sub_file_sender_queue(self):
        return self._sub_file_sender_queue
    
    def get_sub_file_payload_queue(self):
        return self._sub_file_payload_queue

    def _on_client_connect(self, mqtt_client, userdata, flags, rc):
        # sub_prefix = f"{'' if BRIDGE_MOUNTPOINT == '' else '/' if BRIDGE_MOUNTPOINT == '/' else f'{BRIDGE_MOUNTPOINT}/'}{TOPIC_PREFIX}"
        print('connected local broker')
        self._mqtt_client.subscribe(f"+/ECCI/{BROKER_ID}/+/plugin/+/fileManager", qos=2)
        self._mqtt_client.subscribe(f"ECCI/{BROKER_ID}/+/plugin/+/fileManager", qos=2)

    def _on_client_message(self, mqtt_client, userdata, msg):
        rev_msg = cPickle.loads(msg.payload)
        app_id,sender = self._topic_parse(msg.topic)
        if rev_msg['type'] == "file":
            self._sub_file_sender_queue.put([app_id,sender])
            self._sub_file_payload_queue.put(rev_msg['contents'])
    
    def _on_client_publish(self, mqtt_client, userdata, mid):
        print('publish success')
        pass

    def _topic_parse(self, topic):
        app_id,sender = re.findall(r'.*/?ECCI/.*/(.*)/plugin/(.*)/.*',topic)[0]
        return app_id,sender
    
    def initialize(self):
        try:
            self._mqtt_client = mqtt.Client("file_manager")
            self._mqtt_client.on_message = self._on_client_message
            self._mqtt_client.on_connect = self._on_client_connect
            self._mqtt_client.on_publish = self._on_client_publish
            if BROKER_USERNAME and BROKER_PASSWORD:
                self._mqtt_client.username_pw_set(BROKER_USERNAME,BROKER_PASSWORD)
        except TypeError:
            logger.error('Connect to mqtt broker error')
            return

    def run(self):
        try:
            self._mqtt_client.connect(self._broker_ip, self._broker_port)
            self._mqtt_client.loop_start()
        except Exception as e:
            logger.error('Error occurred in event handler: {}'.format(e))
