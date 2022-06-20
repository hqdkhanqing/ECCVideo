# -*- coding: UTF-8 -*-
import re
import paho.mqtt.client as mqtt
import logging
import globalvar as GlobalVar
import json
import os

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def on_connect(client, userdata, flags, rc):
    GlobalVar.set_mq_client(client)
    logger.info("Connected with result code " + str(rc))

def on_subscribe(client, userdata, mid, granted_qos):
    logger.info("subscribe mid " + str(mid))
    logger.info("subscribe granted_qos " + str(granted_qos))
    logger.info("subscribe userdata " + str(userdata))

def on_unsubscribe(client, userdata, mid):
    logger.info("subscribe mid " + str(mid))

def on_message(client, userdata, msg):
    print("sub message")
    logger.info("sub message")
    topic = msg.topic
    logger.info("sub topic="+topic)
    # agent资源状态监控
    pattern_sys = "\$SYS/brokers/.*"

    # 用户 broker资源状态监控
    pattern_broker = "toEdgeAI/broker/.*"

    # 用户 app资源状态监控
    pattern_app = "toEdgeAI/app/.*"

    # 应用内部日志收集
    pattern_app_container = "toEdgeAI/container/.*"

    # 应用控制器ready收集
    pattern_con_cntr_ready = "toEdgeAI/con_cntr_ready/.*"


    try:
        # print("msg payload is ",json.loads(msg.payload))
        # print(type(json.loads(msg.payload)))
        payload = json.loads(msg.payload.decode('utf-8'))
        print(payload)
    except Exception as e:
        print(e)
    
    if re.match(pattern_sys, topic):
        resource_agent = "agent_"
        resource_usermonitor = "usermonitor_"
        
        client_id, status = re.findall(r'.*/(.*)/(.*)', topic)[0]
        print(client_id)
        print(status)
        if re.match(resource_agent,client_id):
            try:
                payload['clientid'] = client_id.split('_')[1]
                print(payload)
            except Exception as e:
                print(e)
            message = {"comm":"mqtt", "type":"agent", "msg":{"payload":payload,"status":status}}
            print("on_message message", message)
            userdata.put(message)
        elif re.match(resource_usermonitor,client_id):
            # TODO(gyf) 预留给usermonitor资源监控，若需要监控的话
            payload['broker_id'] = client_id.split('_')[1]
            message = {"comm":"mqtt", "type":"usermonitor", "msg":{"payload":payload,"status":status}}
            # TODO(gyf) 目前只是获取到，apiserver并没有相关数据库 12.29
            print("usermonitor message", message)
            logger.info("listen usermonitor service container status")

    elif re.match(pattern_broker, topic):
        broker_id = re.findall(r'toEdgeAI/broker/(.*)', topic)[0]
        message = {"comm":"mqtt","type":"broker", "msg":{"online":payload['online'],"broker_id":broker_id}}
        # TODO(gyf): test use
        print("on_message message", message)
        # TODO(gyf) test annotation
        userdata.put(message)
    elif re.match(pattern_app, topic):
        agent_id = re.findall(r'toEdgeAI/app/(.*)', topic)[0]
        logger.info("app agent_id "+agent_id)
        message = {"comm":"mqtt", "type":"app", "msg":payload['appStatus']}
        # TODO(gyf): test use
        print("on_message message", message)
        userdata.put(message)

    elif re.match(pattern_app_container, topic):
        broker_id = re.findall(r'toEdgeAI/container/(.*)', topic)[0] 
        message = {"comm":"mqtt", "type":"container_log", "msg":payload}
        print("on_message message", message)
        userdata.put(message)
    
    elif re.match(pattern_con_cntr_ready, topic):
        broker_id = re.findall(r'toEdgeAI/con_cntr_ready/(.*)', topic)[0] 
        message = {"comm":"mqtt", "type":"con_cntr_ready", "msg":payload}
        print("on_message message", message)
        userdata.put(message)
        
    
    # TODO(gyf) test annotation
    # userdata.put(message)

ECCI_CONTROLLER_MQ_USERNAME = os.getenv("ECCI_CONTROLLER_MQ_USERNAME",default="admin")
ECCI_CONTROLLER_MQ_PASSWORD = os.getenv("ECCI_CONTROLLER_MQ_PASSWORD",default="admin123")
# ECCI_CONTROLLER_MQ_IP = os.getenv("ECCI_CONTROLLER_MQ_IP")
# ECCI_CONTROLLER_MQ_IP = "emqx"
# ECCI_CONTROLLER_MQ_PORT = int(os.getenv("ECCI_CONTROLLER_MQ_PORT",default="1883"))

def mq_main(comm_queue):
    ECCI_CONTROLLER_MQ_IP = os.getenv("ECCI_CONTROLLER_MQ_IP","emqx")
    ECCI_CONTROLLER_MQ_PORT = int(os.getenv("ECCI_CONTROLLER_MQ_PORT",1883))
    client = mqtt.Client(client_id='controller',userdata=comm_queue)
    # client.enable_logger(logger)
    if ECCI_CONTROLLER_MQ_USERNAME and ECCI_CONTROLLER_MQ_PASSWORD:
        client.username_pw_set(ECCI_CONTROLLER_MQ_USERNAME,ECCI_CONTROLLER_MQ_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    # client.on_subscribe= on_subscribe
    client.on_unsubscribe= on_unsubscribe
    client.connect(ECCI_CONTROLLER_MQ_IP, ECCI_CONTROLLER_MQ_PORT, 60)
    try:
        # client.subscribe([("toEdgeAI/broker/#", 2), ("toEdgeAI/app/#", 2),("$SYS/brokers/+/clients/#",2)])
        client.subscribe("toEdgeAI/app/#", 2)
        client.subscribe("toEdgeAI/broker/#", 2)
        client.subscribe("toEdgeAI/container/#", 2)
        client.subscribe("toEdgeAI/con_cntr_ready/#", 2)
        client.subscribe("$SYS/brokers/+/clients/#",2)
    except Exception as e:
        print(e)
        raise Exception("ERROR")
    # client.subscribe(topic="toEdgeAI/broker/#", qos=2)
    # client.subscribe(topic="toEdgeAI/app/#", qos=2)
    # client.subscribe(topic="$SYS/brokers/edgeai@39.99.146.169/clients/#", qos=2)
    client.loop_forever()