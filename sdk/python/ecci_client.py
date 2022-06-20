import paho.mqtt.client as mqtt
import threading
import os
import ast
import re
import _pickle as cPickle
from queue import Queue
import io
from urllib import request
import logging
import mimetypes
import uuid

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

SUB_OBJECTS = os.getenv("ECCI_SUB_OBJECTS",default = None)
PUB_TARGETS = ast.literal_eval(os.getenv("ECCI_PUB_TARGETS",default = "{}"))

BROKER_IP = os.getenv("ECCI_LOCAL_BROKER_IP")
BROKER_PORT = int(os.getenv("ECCI_LOCAL_BROKER_PORT", default="1883"))
BROKER_ID = os.getenv("ECCI_LOCAL_BROKER_ID")
BROKER_USERNAME = os.getenv("ECCI_LOCAL_BROKER_USERNAME")
BROKER_PASSWORD = os.getenv("ECCI_LOCAL_BROKER_PASSWORD")

APP_ID = os.getenv("ECCI_APP_ID")
CONTAINER_NAME = re.findall(r"^edgeai_.*?_(.*)", os.getenv("ECCI_CONTAINER_NAME"))[0]
BRIDGE_MOUNTPOINTS = ast.literal_eval(os.getenv("ECCI_BRIDGE_MOUNTPOINTS",default="[]"))

CONTAINER_TYPE = os.getenv("ECCI_CONTAINER_TYPE")

TOPIC_PREFIX = f"ECCI/{BROKER_ID}/{APP_ID}"

def gen_sub_topic(pub_dict):
    target,target_broker_ip = pub_dict
    return target,f'ECCI/{target_broker_ip}/{APP_ID}/app/{CONTAINER_NAME}/{target}'
if PUB_TARGETS:
    PUB_TOPICS = dict(map(gen_sub_topic,PUB_TARGETS.items()))

def gen_put_file_info(pub_targets):
    put_file_info = dict()
    for item in pub_targets:
        target,target_broker_id = item,pub_targets[item]
        if target_broker_id not in put_file_info:
            put_file_info[target_broker_id] = {}
        topic = f'ECCI/{target_broker_id}/{APP_ID}/plugin/{CONTAINER_NAME}/fileManager'
        put_file_info[target_broker_id][target] = topic
    return put_file_info
PUT_FILE_INFO = gen_put_file_info(PUB_TARGETS)

class MultiPartForm:
    """Accumulate the data to be used when posting a form."""

    def __init__(self):
        self.form_fields = []
        self.files = []
        # Use a large random byte string to separate
        # parts of the MIME data.
        self.boundary = uuid.uuid4().hex.encode('utf-8')
        return

    def get_content_type(self):
        return 'multipart/form-data; boundary={}'.format(
            self.boundary.decode('utf-8'))

    def add_field(self, name, value):
        """Add a simple field to the form data."""
        self.form_fields.append((name, value))

    def add_file(self, fieldname, filename, fileHandle,
                 mimetype=None):
        """Add a file to be uploaded."""
        body = fileHandle.read()
        if mimetype is None:
            mimetype = (
                mimetypes.guess_type(filename)[0] or
                'application/octet-stream'
            )
        self.files.append((fieldname, filename, mimetype, body))
        return

    @staticmethod
    def _form_data(name):
        return ('Content-Disposition: form-data; '
                'name="{}"\r\n').format(name).encode('utf-8')

    @staticmethod
    def _attached_file(name, filename):
        return ('Content-: file; '
                'name="{}"; filename="{}"\r\n').format(
                    name, filename).encode('utf-8')

    @staticmethod
    def _content_type(ct):
        return 'Content-Type: {}\r\n'.format(ct).encode('utf-8')

    def __bytes__(self):
        """Return a byte-string representing the form data,
        including attached files.
        """
        buffer = io.BytesIO()
        boundary = b'--' + self.boundary + b'\r\n'

        # Add the form fields
        for name, value in self.form_fields:
            # buffer.write(boundary)
            # buffer.write(self._form_data(name))
            # buffer.write(b'\r\n')
            buffer.write(value.encode('utf-8'))
            # buffer.write(b'\r\n')

        # Add the files to upload
        for f_name, filename, f_content_type, body in self.files:
            # buffer.write(boundary)
            # buffer.write(self._attached_file(f_name, filename))
            # buffer.write(self._content_type(f_content_type))
            # buffer.write(b'\r\n')
            buffer.write(body)
            # buffer.write(b'\r\n')

        # buffer.write(b'--' + self.boundary + b'--\r\n')
        return buffer.getvalue()

class MqttClient:

    def __init__(self):
        self._broker_ip = BROKER_IP
        self._broker_port = BROKER_PORT
        self.training_start = threading.Event()
        self.training_exit = threading.Event()
        self._sub_data_sender_queue = Queue()
        self._sub_data_payload_queue = Queue()
        self._sub_cmd_sender_queue = Queue()
        self._sub_cmd_payload_queue = Queue()
        self._sub_put_file_dict = dict()
        self._sub_get_file_dict = dict()
        self._file_contents = dict()
        self._mqtt_client = None

    def get_sub_data_sender_queue(self):
        return self._sub_data_sender_queue
    
    def get_sub_data_payload_queue(self):
        return self._sub_data_payload_queue

    def get_sub_cmd_sender_queue(self):
        return self._sub_cmd_sender_queue
    
    def get_sub_cmd_payload_queue(self):
        return self._sub_cmd_payload_queue

    def get_sub_put_file_dict(self):
        return self._sub_put_file_dict

    def get_sub_get_file_dict(self):
        return self._sub_get_file_dict

    def _on_client_connect(self, mqtt_client, userdata, flags, rc):
        if BRIDGE_MOUNTPOINTS:
            for mountpoint in BRIDGE_MOUNTPOINTS:
                sub_prefix = f"{mountpoint}{TOPIC_PREFIX}"
                self._mqtt_client.subscribe(f"{sub_prefix}/app/+/{CONTAINER_NAME}", qos=2)
                self._mqtt_client.subscribe(f"{sub_prefix}/plugin/+/{CONTAINER_NAME}", qos=2)
        self._mqtt_client.subscribe(f"{TOPIC_PREFIX}/app/+/{CONTAINER_NAME}", qos=2)
        self._mqtt_client.subscribe(f"{TOPIC_PREFIX}/plugin/+/{CONTAINER_NAME}", qos=2)

        if SUB_OBJECTS != None:
            sub_objects = ast.literal_eval(SUB_OBJECTS)
            for sub_object  in sub_objects:
                self._mqtt_client.subscribe(f"{TOPIC_PREFIX}/app/+/{sub_object}", qos=2)
                self._mqtt_client.subscribe(f"{TOPIC_PREFIX}/plugin/+/{sub_object}", qos=2)


    def _on_client_message(self, mqtt_client, userdata, msg):
        rev_msg = cPickle.loads(msg.payload)
        sender = self._topic_parse(msg.topic)
        if rev_msg['type'] == "cmd":
            self._sub_cmd_sender_queue.put(sender)
            self._sub_cmd_payload_queue.put(rev_msg['contents'])
            try:
                if rev_msg['contents']['cmd'] == "start":
                    self.training_start.set()
                elif rev_msg['contents']['cmd'] == "exit":
                    self.training_exit.set()
            except KeyError as e:
                pass
        elif rev_msg['type'] == "data":
            self._sub_data_sender_queue.put(sender)
            self._sub_data_payload_queue.put(rev_msg['contents'])
        elif rev_msg['type'] == "file":
            if rev_msg['contents']['cmd'] == 'resPutURL': 
                file_name = rev_msg['contents']['file_name']
                putURL = rev_msg['contents']['putURL']
                if 'file_path' in rev_msg['contents']:
                    file_path = rev_msg['contents']['file_path']
                    self.upload_file(putURL, file_name, file_path = file_path)
                else:
                    try:
                        contents = self._file_contents[file_name]
                        self.upload_file(putURL, file_name, contents = contents)
                    except Exception as e:
                        pass
                # if file_name not in self._sub_put_file_dict:
                #     self._sub_put_file_dict[file_name] = []
                # self._sub_put_file_dict[file_name] = putURL
                self._sub_put_file_dict[file_name] = {'putURL':putURL,'is_transfered':False}
            elif rev_msg['contents']['cmd'] == 'resTransfer':
                file_name = rev_msg['contents']['file_name']
                getURL = rev_msg['contents']['getURL']
                self._sub_get_file_dict[file_name] = getURL
    
    def _on_client_publish(self, mqtt_client, userdata, mid):
        self._sub_put_file_dict[userdata]['is_transfered'] = True

    def download_file(self, file_path, getURL):
        f = request.urlopen(getURL) 
        with open(file_path, "wb") as code: 
            code.write(f.read())

    def download_contents(self, getURL):
        f = request.urlopen(getURL) 
        return cPickle.loads(f.read())

    # kwargs has key: object_path or contents
    def upload_file(self, puturl, object_name, **kwargs):
        form = MultiPartForm()
        if 'contents' in kwargs:
            form.add_file(
                'contents', object_name,
                fileHandle=io.BytesIO(cPickle.dumps(self._file_contents[object_name])))
        elif 'file_path' in kwargs:
            form.add_file(
                'contents', object_name,
                fileHandle=open(kwargs['file_path'],'rb'))
        data = bytes(form)
        r = request.Request(puturl, data=data,method='PUT')
        r.add_header('Content-type', form.get_content_type())
        r.add_header('Content-length', len(data))
        request.urlopen(r)

    def find_target(self, targets):
        target_list=[]
        if isinstance(targets,str):
            for pub_target in list(PUB_TARGETS.keys()):
                if pub_target.startswith(targets):
                    target_list.append(pub_target)
        elif isinstance(targets,list):
            for target in targets:
                for pub_target in list(PUB_TARGETS.keys()):
                    if pub_target.startswith(target):
                        target_list.append(pub_target)
        return target_list

    def publish(self, message, targets=None, retain=False):
        no_match = True
        try:
            if targets == None:
                for topic in list(PUB_TOPICS.values()):
                    self._mqtt_client.publish(topic=topic, payload=cPickle.dumps(message), qos=2, retain=retain)
                no_match = False
            elif isinstance(targets,str) or isinstance(targets,list):
                target_list = self.find_target(targets)
                if len(target_list) != 0:
                    no_match = False
                for target_item in target_list:
                    self._mqtt_client.publish(topic=PUB_TOPICS[target_item], payload=cPickle.dumps(message), qos=2, retain=retain)
            else:
                logger.critical(f"Illegal targets format which is {str(type(targets))}")
            if no_match:
                logger.critical(f"refused publish, {targets} does not exist in the {PUB_TOPICS}")
        except Exception as e:
            logger.error(e)

    def transfer(self, filename, targets):
        file_name = filename
        target_list = self.find_target(targets)
        try:
            if isinstance(targets,str) or isinstance(targets,list):
                broker_dict = dict()
                for broker_item in PUT_FILE_INFO:
                    broker_target_list = []
                    for target in target_list:
                        if target in PUT_FILE_INFO[broker_item]:
                            broker_target_list.append(target)
                    if len(broker_target_list)!=0:
                        broker_dict[broker_item] = broker_target_list
                if CONTAINER_TYPE == 'cloud':
                    topic = f'ECCI/{BROKER_ID}/{APP_ID}/plugin/{CONTAINER_NAME}/fileManager'
                    message = {'type':'file','contents':{'cmd':'reqTransfer','file_name':file_name,\
                        'target':broker_dict}}
                    self._mqtt_client.publish(topic=topic, payload=cPickle.dumps(message), qos=2)
                    self._mqtt_client.user_data_set(file_name)
                elif CONTAINER_TYPE == 'edge':
                    for target_broker in broker_dict:
                        topic = f'ECCI/{target_broker}/{APP_ID}/plugin/{CONTAINER_NAME}/fileManager'
                        message = {'type':'file','contents':{'cmd':'reqTransfer','file_name':file_name,\
                            'target':{target_broker:broker_dict[target_broker]}}}
                        self._mqtt_client.publish(topic=topic, payload=cPickle.dumps(message), qos=2)
            else:
                logger.critical(f"refused publish, {targets} does not exist in the {PUB_TOPICS}")
        except Exception as e:
            logger.error(e)

    def putHandler(self, filename, targets, filepath=None, contents=None):
        target_list = self.find_target(targets)
        try:
            if isinstance(targets,str) or isinstance(targets,list):
                broker_dict = dict()
                for broker_item in PUT_FILE_INFO:
                    broker_target_list = []
                    for target_item in target_list:
                        if target_item in PUT_FILE_INFO[broker_item]:
                            broker_target_list.append(target_item)
                    if len(broker_target_list)!=0:
                        broker_dict[broker_item] = broker_target_list
                if filepath:
                    message = {'type':'file','contents':{'cmd':'reqPutURL','source_broker_id':BROKER_ID,'file_name':filename,'file_path':filepath}}
                elif contents:
                    self._file_contents[filename] = contents
                    message = {'type':'file','contents':{'cmd':'reqPutURL','source_broker_id':BROKER_ID,'file_name':filename}}
                if CONTAINER_TYPE == 'cloud':
                    topic = f'ECCI/{BROKER_ID}/{APP_ID}/plugin/{CONTAINER_NAME}/fileManager'
                    self._mqtt_client.publish(topic=topic, payload=cPickle.dumps(message), qos=2)
                elif CONTAINER_TYPE == 'edge':
                    for target_broker in broker_dict:
                        topic = f'ECCI/{target_broker}/{APP_ID}/plugin/{CONTAINER_NAME}/fileManager'
                        self._mqtt_client.publish(topic=topic, payload=cPickle.dumps(message), qos=2)
            else:
                logger.critical(f"refused publish, {targets} does not exist in the {PUB_TOPICS}")
        except Exception as e:
            logger.error(e)

    def _topic_parse(self, topic):
        if BRIDGE_MOUNTPOINTS:
            for mountpoint in BRIDGE_MOUNTPOINTS:
                pattern = f"^{mountpoint}"
                if re.match(pattern,topic):
                    sender = re.findall(r'^(?:'+mountpoint+')?/?ECCI/.*/.*/.*/(.*)/.*',topic)[0]
                    return sender
        sender = re.findall(r'^ECCI/.*/.*/.*/(.*)/.*',topic)[0]
        return sender
        
    
    def initialize(self):
        
        try:
            self._mqtt_client = mqtt.Client()
            self._mqtt_client.on_message = self._on_client_message
            self._mqtt_client.on_connect = self._on_client_connect
            self._mqtt_client.on_publish = self._on_client_publish
        except TypeError:
            logger.error('Connect to mqtt broker error')
            return

    def run(self):
        try:
            if BROKER_USERNAME and BROKER_PASSWORD:
                self._mqtt_client.username_pw_set(BROKER_USERNAME,BROKER_PASSWORD)
            self._mqtt_client.connect(self._broker_ip, self._broker_port)
            self._mqtt_client.loop_start()
        except Exception as e:
            logger.error('Error occurred in event handler: {}'.format(e))

if __name__ == "__main__":
    