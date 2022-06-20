import paho.mqtt.client as mqtt
import json

# def mq_send(msg,conf,mold):
#     conf['url'] = conf['url']+mold+"/${broker_id}"
#     mq_send_msg(msg,conf)

# def mq_send_msg(message,conf):
#     print("mq send")
#     print(conf)
#     try:
#         print("topic ",conf['url'])
#         print("payload ", message)
#     except Exception as e:
#         print(e)
#     client = mqtt.Client(client_id = "monitor-broker_id")
#     client.connect(conf['ip'], int(conf['port']), 60)
#     client.loop_start()
#     client.publish(conf['url'], json.dumps(message), 2)
#     client.loop_stop()



# -*- coding: UTF-8 -*-
import re
import paho.mqtt.client as mqtt
import logging
import globalvar as GlobalVar
import os
# from utils import get_conf

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

ECCI_MONITOR_FORWARD_BROKER_ID = os.getenv("ECCI_MONITOR_FORWARD_BROKER_ID")
ECCI_MONITOR_MODE = os.getenv("ECCI_MONITOR_MODE")

def on_connect(client, userdata, flags, rc):
    print("connect status", rc)
    if ECCI_MONITOR_MODE != "system" and ECCI_MONITOR_MODE != "user":
        logger.critical(f"Unknown monitor pattern {ECCI_MONITOR_MODE}")
        os._exit(0)
    GlobalVar.set_sub_client(client)
    logger.info("Connected with result code " + str(rc))
    ECCI_MONITOR_SOURCE_SUB_TOPIC = os.getenv("ECCI_MONITOR_SOURCE_SUB_TOPIC",default="")
    # ECCI_MONITOR_MODE = os.getenv("ECCI_MONITOR_MODE")
    if ECCI_MONITOR_MODE == "system" and ECCI_MONITOR_SOURCE_SUB_TOPIC == "":
        # ECCI_MONITOR_SOURCE_SUB_TOPIC = "toEdgeAI/monitor/#"
        client.subscribe("toEdgeAI/monitor/#")
    if ECCI_MONITOR_MODE == "user" and ECCI_MONITOR_SOURCE_SUB_TOPIC == "":
        # ECCI_MONITOR_SOURCE_SUB_TOPIC = "$SYS/brokers/+/version"
        client.subscribe("$SYS/brokers/+/version")
        logger.debug(f"ECCI_MONITOR_FORWARD_BROKER_ID={ECCI_MONITOR_FORWARD_BROKER_ID}")
        # print("sub log"+f"toEdgeaAI/{ECCI_MONITOR_FORWARD_BROKER_ID}/log")
        client.subscribe(f"toEdgeAI/{ECCI_MONITOR_FORWARD_BROKER_ID}/log")
        # 订阅 应用controller就绪 topic,收到消息后转发到ECCI 系统中
        client.subscribe(f"toEdgeAI/{ECCI_MONITOR_FORWARD_BROKER_ID}/con_cntr_ready")
    

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Unexpected disconnection.")
        forwarded_msg = {"type":"broker","online":False}
        userdata.put(forwarded_msg)

def on_publish(client, userdata, mid):
    print("publish success")

def on_subscribe(client, userdata, mid, granted_qos):
    logger.info("subscribe mid " + str(mid))
    logger.info("subscribe granted_qos " + str(granted_qos))
    logger.info("subscribe userdata " + str(userdata))

def on_unsubscribe(client, userdata, mid):
    logger.info("subscribe mid " + str(mid))

def on_message(client, userdata, msg):
    topic = msg.topic
    print(msg.payload)
    payload = msg.payload.decode("utf-8")
    print("on_message ",topic)
    print(payload)
    if ECCI_MONITOR_MODE == "user":
        print("user monitor")
        pattern_heartbeat = "\$SYS/brokers/.*/version"
        pattern_appcontainerslog = f"toEdgeAI/{ECCI_MONITOR_FORWARD_BROKER_ID}/log"
        pattern_con_cntr_ready = f"toEdgeAI/{ECCI_MONITOR_FORWARD_BROKER_ID}/con_cntr_ready"
        # pattern_connect = "\$SYS/brokers/.*/clients/.*/.*"
        print(re.match(pattern_heartbeat, topic))
        # print(re.match(pattern_connect, topic))
        if re.match(pattern_heartbeat, topic):
            forwarded_msg = {"type":"broker","online":True}
        # elif re.match(pattern_connect, topic):
        #     try:

        #         client_id, conn_status = re.findall(r'\$SYS/brokers/.*/clients/(.*)/(.*)', topic)[0]
        #         # 从client_id 中split出app_id agent_id container_name
        #         status = True if conn_status=="connected" else False
        #         forwarded_msg = {"app_id":"${app_id}", "agent_id":"${agent_id}", "container_name":"${container_name}", "online":status}
        #         print("app status ",msg)
        #     except Exception as e:
        #         print(e)
        # send_msg(msg,pattern=pattern,mold=mold)
        elif re.match(pattern_appcontainerslog, topic):
            logger.info("receive app container log message")
            forwarded_msg = json.loads(msg.payload)
            forwarded_msg.update({"type":"container"})
            
        elif re.match(pattern_con_cntr_ready, topic):
            logger.info("receive controller container ready message")
            forwarded_msg = json.loads(msg.payload)
            forwarded_msg.update({"type":"con_cntr_ready"})
        else:
            logger.critical("Unknown topic "+str(topic))
        userdata.put(forwarded_msg)

    elif ECCI_MONITOR_MODE == "system":
        print("on_message")
        try:
            topic = msg.topic
            print(msg.payload)
            payload = json.loads(msg.payload.decode("utf-8"))
            print(topic)
            print(payload)
            # payload = msg.payload
            # send_msg("data",payload)

        except Exception as e:
            print(e)
        agent_id = re.findall(r'toEdgeAI/monitor/(.*)', topic)[0]
        print(agent_id)
        payload['agent_id'] = agent_id
        # routing_msg = {"msg":payload}
        # print("ws_msg = ", payload)
        # send_msg(msg,pattern=pattern, mold=mold)
        try:
            msg_type = "monitor.data"
            forwarded_msg = {"type":msg_type,"msg":payload}
            userdata.put(forwarded_msg)
        except Exception as e:
            print(e)
    


def mq_sub_main(comm_queue):
    print("mq_sub_main")
    ECCI_MONITOR_SOURCE_IP = os.getenv("ECCI_MONITOR_SOURCE_IP",default="emqx")
    ECCI_MONITOR_SOURCE_PORT = int(os.getenv("ECCI_MONITOR_SOURCE_PORT",default="1883"))
    ECCI_MONTTOR_SOURCE_USERNAME = os.getenv("ECCI_MONTTOR_SOURCE_USERNAME",default="admin")
    ECCI_MONITOR_SOURCE_PASSWORD = os.getenv("ECCI_MONITOR_SOURCE_PASSWORD",default="admin123")
    # ECCI_MONITOR_SOURCE_SUB_TOPIC = os.getenv("ECCI_MONITOR_SOURCE_SUB_TOPIC")
    ECCI_MONITOR_MODE = os.getenv("ECCI_MONITOR_MODE")
    # if ECCI_MONITOR_MODE == "system" and ECCI_MONITOR_SOURCE_SUB_TOPIC == None:
    #     ECCI_MONITOR_SOURCE_SUB_TOPIC = "toEdgeAI/monitor/#"
    # if ECCI_MONITOR_MODE == "user" and ECCI_MONITOR_SOURCE_SUB_TOPIC == None:
    #     ECCI_MONITOR_SOURCE_SUB_TOPIC = "$SYS/brokers/+/version"
    # else:
    #     logger.critical(f"Unknown monitor pattern {ECCI_MONITOR_MODE}")
    #     os._exit(0)
    
    client = mqtt.Client(client_id=f"{ECCI_MONITOR_MODE}_monitor",userdata=comm_queue)
    # client.enable_logger(logger)
    # conf = get_conf("source","monitor")
    # logger.debug("conf is "+str(conf))
    if ECCI_MONTTOR_SOURCE_USERNAME and ECCI_MONITOR_SOURCE_PASSWORD:
        client.username_pw_set(ECCI_MONTTOR_SOURCE_USERNAME,ECCI_MONITOR_SOURCE_PASSWORD)
    if ECCI_MONITOR_MODE == "user":
        client.username_pw_set("dashboard","dashboard")
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.on_publish = on_publish
    try:
        client.connect(ECCI_MONITOR_SOURCE_IP, ECCI_MONITOR_SOURCE_PORT, 60)
    except ConnectionRefusedError as e:
        logger.critical(str(e))
        forwarded_msg = {"type":"broker","online":False}
        comm_queue.put(forwarded_msg)
        # send_msg(msg=msg,pattern="status",mold="broker")
        os._exit(0)
        
    # client.subscribe([("toEdgeAI/broker/#", 0), ("toEdgeAI/app/#", 0),("$SYS/brokers/gyf-virtual-machine@192.168.79.201/clients/#",2)])
    # client.subscribe(conf['topic'])
    # client.subscribe(topic="req/#", qos=0)
    client.loop_forever()



def mq_forward_main():
    ECCI_MONITOR_FORWARD_USERNAME = os.getenv("ECCI_MONITOR_FORWARD_USERNAME")
    ECCI_MONITOR_FORWARD_PASSWORD = os.getenv("ECCI_MONITOR_FORWARD_PASSWORD")
    ECCI_MONITOR_FORWARD_IP = os.getenv("ECCI_MONITOR_FORWARD_IP")
    ECCI_MONITOR_FORWARD_PORT = int(os.getenv("ECCI_MONITOR_FORWARD_PORT"))
    ECCI_MONITOR_FORWARD_BROKER_ID = os.getenv("ECCI_MONITOR_FORWARD_BROKER_ID")
    # 用户monitor 长连接EdgeAI broker以便监控该资源，然后等待调用发送pub请求。
    # conf = get_conf('destination')
    client = mqtt.Client(client_id=f"usermonitor_{ECCI_MONITOR_FORWARD_BROKER_ID}")
    client.on_publish = on_publish
    if ECCI_MONITOR_FORWARD_USERNAME and ECCI_MONITOR_FORWARD_PASSWORD:
        client.username_pw_set(ECCI_MONITOR_FORWARD_USERNAME,ECCI_MONITOR_FORWARD_PASSWORD)
    if ECCI_MONITOR_FORWARD_IP and ECCI_MONITOR_FORWARD_PORT:
        client.connect(ECCI_MONITOR_FORWARD_IP, ECCI_MONITOR_FORWARD_PORT, 60)
    else:
        logger.critical("provide the necessary delivery IP and port")
    GlobalVar.set_forward_client(client)
    client.loop_forever()


def mqtt_send(msg):
    client = GlobalVar.get_forward_client()
    # topic = conf['url']+"broker/"+"c86b293e-0c08-11ea-90b4-00163e968a07"
    print("mqtt_send   "+str(msg))
    topic_type = msg.pop('type',None)
    print("topic_type="+topic_type)
    if topic_type != None:
        topic = f"toEdgeAI/{topic_type}/{ECCI_MONITOR_FORWARD_BROKER_ID}"
    if client != None:
        print("topic=",topic)
        client.publish(topic, json.dumps(msg), 2)
    else:
        print("forward client not ready")