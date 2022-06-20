# -*- coding: UTF-8 -*-
import re
import logging
import os
import _pickle as cPickle
from utils import upload_file
from ecci_client import MqttClient
from minio import Minio
from datetime import timedelta
from minio.error import (ResponseError, BucketAlreadyOwnedByYou,
                         BucketAlreadyExists)
import urllib.request

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

ECCI_MINIO_IP = os.getenv("ECCI_MINIO_IP")
ECCI_MINIO_PORT = os.getenv("ECCI_MINIO_PORT", default=9000)
ECCI_MINIO_ACCESS_KEY = os.getenv("ECCI_MINIO_ACCESS_KEY")
ECCI_MINIO_SECRET_KEY = os.getenv("ECCI_MINIO_SECRET_KEY")
ECCI_MINIO_MODE = os.getenv("ECCI_MINIO_MODE")
ECCI_BROKER_ID = os.getenv("ECCI_BROKER_ID")

def reqPutURL(bucket_name,object_name):
    try:
        return minioClient.presigned_put_object(bucket_name,object_name,expires=timedelta(days=1))
    except ResponseError as err:
        print(err)

def reqGetURL(bucket_name,object_name):
    try:
        return minioClient.presigned_get_object(bucket_name, object_name, expires=timedelta(days=2))
    except ResponseError as err:
        print(err)

if __name__ == "__main__":
    mqtt_client = MqttClient()
    mqtt_client.initialize()
    mqtt_client.run()
    minioClient = Minio(str(ECCI_MINIO_IP)+':'+str(ECCI_MINIO_PORT),access_key=ECCI_MINIO_ACCESS_KEY,secret_key=ECCI_MINIO_SECRET_KEY,secure=False)
    while True:
        msg = mqtt_client.get_sub_file_payload_queue().get()
        app_id,sender = mqtt_client.get_sub_file_sender_queue().get()
        bucket_name = app_id.lower()
        object_name = msg['file_name']
        if msg['cmd'] == 'reqPutURL':
            source_container = sender
            source_broker = msg['source_broker_id']
            print('receive reqPutURL')
            try:
                minioClient.make_bucket(bucket_name)
            except BucketAlreadyOwnedByYou as err:
                pass
            except BucketAlreadyExists as err:
                pass
            except ResponseError as err:
                raise
            finally:
                putURL = reqPutURL(bucket_name,object_name)
                if 'file_path' in msg:
                    message = {'type':'file','contents':{'cmd':'resPutURL','file_name':object_name,'putURL':putURL,'file_path':msg['file_path']}}
                else:
                    message = {'type':'file','contents':{'cmd':'resPutURL','file_name':object_name,'putURL':putURL}}

                topic = f'ECCI/{source_broker}/{app_id}/plugin/fileManager/{source_container}'
                mqtt_client._mqtt_client.publish(topic=topic, payload=cPickle.dumps(message), qos=2)
                print('receive reqPutURL and pub topic:'+topic)
        elif msg['cmd'] == 'reqTransfer':
            print('receive reqTransfer')
            getURL = reqGetURL(bucket_name,object_name)
            for each_target_broker in msg['target']:
                if ECCI_MINIO_MODE=='cloud' and each_target_broker != ECCI_BROKER_ID and len(msg['target'][each_target_broker])>1:
                    message = {'type':'file','contents':{'cmd':'resTransfer','target':msg['target'][each_target_broker],'file_name':object_name,'getURL':getURL}}
                    topic = f'ECCI/{each_target_broker}/{app_id}/plugin/fileManager/fileManager'
                    mqtt_client._mqtt_client.publish(topic=topic, payload=cPickle.dumps(message), qos=2)
                    print('receive reqTransfer and pub topic:'+topic)
                else:
                    for each_container in msg['target'][each_target_broker]:
                        message = {'type':'file','contents':{'cmd':'resTransfer','file_name':object_name,'getURL':getURL}}
                        topic = f'ECCI/{each_target_broker}/{app_id}/plugin/fileManager/{each_container}'
                        mqtt_client._mqtt_client.publish(topic=topic, payload=cPickle.dumps(message), qos=2)
                        print('receive reqTransfer and pub topic:'+topic)
        elif ECCI_MINIO_MODE=='edge' and msg['cmd'] == 'resTransfer':
            print('receive resTransfer')
            file_name = msg['file_name']
            f = urllib.request.urlopen(msg['getURL'])
            try:
                minioClient.make_bucket(bucket_name)
            except BucketAlreadyOwnedByYou as err:
                pass
            except BucketAlreadyExists as err:
                pass
            except ResponseError as err:
                raise
            finally:
                putURL = reqPutURL(bucket_name,object_name)
                upload_file(putURL,object_name,object_path=f)
                getURL = reqGetURL(bucket_name,object_name)
                for each_container in msg['target']:
                    message = {'type':'file','contents':{'cmd':'resTransfer','file_name':object_name,'getURL':getURL}}
                    topic = f'ECCI/{ECCI_BROKER_ID}/{app_id}/plugin/fileManager/{each_container}'
                    mqtt_client._mqtt_client.publish(topic=topic, payload=cPickle.dumps(message), qos=2)
                    print('receive resTransfer and pub topic:'+topic)

