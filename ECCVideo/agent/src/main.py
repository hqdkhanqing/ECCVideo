#-*-coding: UTF-8 -*-
import re
import paho.mqtt.client as mqtt
import time
from multiprocessing import Process
from threading import Thread
import queue
import uuid
# from utils import *
# from handle_sub import wait_to_handle
from collect_data import *
# import configparser
# import argparse
import os
import json
import logging
# from handle_sub import compose_handle
from app_deploy import compose_handle
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# cf = configparser.ConfigParser()

ECCI_BROKER_IP = os.getenv("ECCI_BROKER_IP", default="localhost")
ECCI_BROKER_PORT = int(os.getenv("ECCI_BROKER_PORT", default="1883"))
ECCI_AGENT_ID = os.getenv("ECCI_AGENT_ID")
ECCI_MQTT_CLIENT_ID = os.getenv("ECCI_MQTT_CLIENT_ID", default=ECCI_AGENT_ID)

# 认证
## 用户名密码认证
ECCI_USERNAME = os.getenv("ECCI_USERNAME")
ECCI_PASSWORD = os.getenv("ECCI_PASSWORD")



def on_connect(client, userdata, flags, rc):
    logger.info("Connected with result code " + str(rc))
    if rc == 5:
        logger.critical("auth failed")
        os._exit(0)
    client.subscribe(f"toAgent/{ECCI_AGENT_ID}/#",2)


def on_disconnect(client, userdata, rc):
    logger.info("Device disconnected with result code: " + str(rc))

def on_subscribe(client, userdata, mid, granted_qos):
    print("on_subscribe mid", mid)
    print("on_subscribe client", client)
    print("on_subscribe granted_qos", granted_qos)
    collect_data = Thread(target=collect_data_func, args=(client,))
    logger.debug("on_subscribe client id"+str(id(client)))
    collect_data.start()


def on_message(client, userdata, msg):
    # print(msg.topic+" "+str(msg.payload))
    logger.debug("============="+msg.topic)
    # logger.info("--------------------handler received")
    # cf.read("./data/configs/config.ini")
    # agentID = cf.get("auth", "agentid")
    # emqx_edge_broker = cf.get("mqtt", "emqx_edge_broker")
    # MQTT_IP = '' if not emqx_edge_broker else emqx_edge_broker.split(':')[0]
    # MQTT_PORT = '' if not emqx_edge_broker else int(emqx_edge_broker.split(':')[1])


    pattern, operate = re.findall(r'toAgent/.*/(.*)/(.*)', msg.topic)[0]

    logger.info("agent handle parse="+pattern+","+operate)
    logger.debug("===========msg.payload="+str(msg.payload.decode('utf-8')))
    # payload_info = eval(msg.payload.decode('utf-8'))
    try:
        payload_info = json.loads(msg.payload.decode('utf-8'))
        print(type(payload_info))
    except Exception as e:
        print(e)
    if pattern == "app":
        app_id = payload_info['app_id']

        # responseTopic = 'toDP/broker_id/app_manange_success/'+payload_info['app_id']
        # data = {'time': time.ctime(), 'app_id': app_id}
        # payload = json.dumps(data)

        # logger.info("======before pub")
        # client.publish(responseTopic, payload, 2)
        # pub(responseTopic, payload, MQTT_IP, MQTT_PORT)
        # logger.info("======after pub")

        if operate == 'up':
            import compose_encapsulation
            compose_yml = payload_info['yml']
            compose_encapsulated_compose = compose_encapsulation.compose_encapsulate(app_id,compose_yml)
            print("compose yaml type", type(compose_encapsulated_compose))
            # ymlTime = payload_info['ymlTime']
            logger.debug(compose_encapsulated_compose)
            # logger.info("=====ymlTime="+ymlTime)
            if "compose_type" in payload_info:
                compose_type = payload_info["compose_type"]
                compose_handle(app_id, operate, compose_encapsulated_compose,compose_type)
            else:
                compose_handle(app_id, operate, compose_encapsulated_compose)
            logger.debug("app_id"+str(app_id))
            logger.debug("operate"+operate)
        elif operate == "start":
            if "compose_type" in payload_info:
                compose_type = payload_info["compose_type"]
                compose_handle(app_id, operate,compose_type=compose_type)
            else:
                compose_handle(app_id, operate)
        else:
            logger.debug("app_id"+str(app_id))
            logger.debug("operate"+operate)
            compose_handle(app_id, operate)
    elif pattern == "agent":
        logger.info("device operate")
        # logger.debug("device operate response")
        # logger.debug("pub response")
        # responseTopic = 'toDP/broker_id/device_manage_success/'+payload_info['device_id']
        # logger.debug(type(payload_info['device_id']))
        # data = {'time': time.ctime(), 'device_id': payload_info['device_id']}
        # payload = json.dumps(data)
        # try:
        #     # pub(responseTopic, payload, MQTT_IP, MQTT_PORT)
        # except Exception as e:
        #     print(e)
        #     raise("error")
        
        # logger.info("pub end")
        if operate == 'delete':
            # logger.info("===delete device config")
            # for temp in os.listdir("./data/configs/"):
            #     os.remove("./data/configs/" + temp)
            try:
                logger.info("===========Program Terminate===========")
                os._exit(0)
            except:
                logger.info("===========Others===========")


def on_publish(client, userdata, mid):
    logger.info("Device sent message")

def collect_data_func(client):
    logger.debug("collect_data_func client id"+str(id(client)))
    # agentID = get_conf("auth")['agentid']
    client.on_publish = on_publish
    # clientCollect.will_set('test/rensanning/will', 'Last will message', 2, False)
    while 1:
        container_data,app_status_data = get_container_info(ECCI_AGENT_ID)
        device_data = get_host_info(ECCI_AGENT_ID)
        collected_data = {"agent_id": ECCI_AGENT_ID, "app":container_data,"agent":device_data}
        client.publish('toEdgeAI/monitor/' + ECCI_AGENT_ID, json.dumps(collected_data), 2)
        
        if len(app_status_data) != 0:
            app_data = {"appStatus":app_status_data}
            client.publish('toEdgeAI/app/' + ECCI_AGENT_ID, json.dumps(app_data), 2)
            print(app_status_data)
        print(container_data)
        print(device_data)
        time.sleep(30)

if __name__ == "__main__":
    # 改为环境变量形式实现-----------------------------
    # config_ini()
    # parser = argparse.ArgumentParser()
    # parser.add_argument("-b", "--broker", help="Emqx Broker ip")
    # parser.add_argument("-P", "--port", help="Emqx Broker port")
    # parser.add_argument("-c", "--clientid", help="Mqtt Client id")
    # parser.add_argument("-t", "--topic", help="prefix topic",default="toAgent/#")
    # parser.add_argument("-a", "--agentid", help="agent's unique identifier")
    # parser.add_argument("-u", "--username", help="specify the user name of the api server")
    # parser.add_argument("-p", "--password", help="specify the user password of the api server")
    
    # args = parser.parse_args()
    # set_ini(args)
    # conf = get_conf("mqtt","auth")
    # logger.debug("conf is "+str(conf))
    logger.debug("ECCI_BROKER_IP="+str(ECCI_BROKER_IP))
    logger.debug("ECCI_BROKER_PORT="+str(ECCI_BROKER_PORT))
    logger.debug("ECCI_AGENT_ID="+str(ECCI_AGENT_ID))
    logger.debug("ECCI_MQTT_CLIENT_ID="+str(ECCI_MQTT_CLIENT_ID))
    logger.debug("ECCI_USERNAME="+str(ECCI_USERNAME))
    logger.debug("ECCI_PASSWORD="+str(ECCI_PASSWORD))

    # client_id = "agent_"+conf['clientid']
    client_id = f"agent_{ECCI_MQTT_CLIENT_ID}"
    client = mqtt.Client(client_id = client_id)
    # client.enable_logger(logger)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_subscribe = on_subscribe
    if ECCI_USERNAME is not "" and ECCI_PASSWORD is not "":
        client.username_pw_set(ECCI_USERNAME,ECCI_PASSWORD)
    client.connect(ECCI_BROKER_IP, ECCI_BROKER_PORT, 60)
    # client.subscribe(topic="req/#", qos=0)
    client.loop_forever()