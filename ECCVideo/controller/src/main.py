from threading import Thread
import queue
from websocketComm import ws_main
from mqttComm import mq_main
import globalvar as GlobalVar 
import time
import asyncio
import json
from parse_topology import parse_app_topology
from utils import distribute_to_agent
import re
import os
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

q = queue.Queue()

ws_listen = Thread(target=ws_main,args=(q,))
ws_listen.start()

mq_listen = Thread(target=mq_main,args=(q,))
mq_listen.start()

# 向服务器端发送认证后的消息
async def send_msg(websocket,msg):
    print("type msg ", type(msg))
    print("msg ", msg)
    send_text = json.dumps(msg)
    print("before websocket.send")
    await websocket.send(send_text)

# while True:
#     try:
        
#         msg = q.get()
#         if msg != None:
#             print("main thread websocket id ", id(GlobalVar.get_ws_client()))
#             print("comm message is ",msg)
#             await send_msg(GlobalVar.get_ws_client(),msg)
#     except Exception as e:
#         print("error is ", e)
#         break


# TODO(gyf): wait test
async def websocket_handler(ws_msg):
    print("enter websocket_handler function")
    (ws_type,ws_command) = ws_msg['type'].split('.')
    if ws_type == "operate":
        (ws_resource,ws_operate) = ws_command.split('_')
        if ws_resource == "app":
            if ws_operate == "up":
                if not os.path.exists("./data/"+ws_msg['msg']['app_id']):
                    print("create app_id fold for compose file")
                    os.makedirs("./data/"+ws_msg['msg']['app_id'])
                
                await parse_app_topology(ws_msg['msg'])
            # print("type websocket_handler ", type(msg))
            # print("before send_msg")
            # await send_msg(GlobalVar.get_ws_client(),msg)
            elif ws_operate == "start":
                await distribute_to_agent(ws_resource, ws_msg['msg']['app_id'], ws_operate,ws_msg['msg']['physical_topology']['agents'], ws_msg['msg']['parser_type'])
                # def distribute_to_agent(type,operate,resources):
            elif ws_operate == "stop":
                await distribute_to_agent(ws_resource, ws_msg['msg']['app_id'], ws_operate,ws_msg['msg']['physical_topology']['agents'])
            elif ws_operate == "down":
                await distribute_to_agent(ws_resource, ws_msg['msg']['app_id'], ws_operate,ws_msg['msg']['physical_topology']['agents'])
            elif ws_operate == "clean":
                await distribute_to_agent(ws_resource, ws_msg['msg']['app_id'], ws_operate,ws_msg['msg']['physical_topology']['agents'])
            elif ws_operate == "delete":
                await distribute_to_agent(ws_resource, ws_msg['msg']['app_id'], ws_operate,ws_msg['msg']['physical_topology']['agents'])
            else:
                logger.critical("Unknown operation "+ws_operate)
        elif ws_resource == "agent":
            if ws_operate == "delete":
                await distribute_to_agent(ws_resource, ws_msg['msg']['agent_id'], ws_operate)

    # if ws_type == "res":
    #     if ws_operate == "physical_topology":
    #         parse_app_topology(ws_msg['msg'])
    #         distribute_to_agent()
    #         # for dirpath,dirnames,filenames in os.walk("./data/"+ws_msg['msg']['app_id']):
    #         #     for file in filenames:
    #         #         fullpath = os.path.join(dirpath,file)
    #         #         topic = 'toAgent/'+re.findall('device-(.*).yml', fullpath)[0]+'/app/create'
    #         #         payload = {}
    #         #         payload['app_id'] = ws_msg['msg']['app_id']
    #         #         with open(fullpath,'r') as f:
    #         #             ymlcontent = f.read()
    #         #         payload['yml'] = ymlcontent
    #         #         pub_msg(topic,payload)


async def mqtt_handler(msg):
    print(msg)
    if msg["type"] == "agent":
        online = True if msg["msg"]['status'] == "connected" else False
        reason = "" if msg["msg"]['status'] == "connected" else "program_exception" if msg['msg']['payload']['reason'] == "closed" else "network_exception"
        print("online ",online)
        print("reason ",reason)
        print(msg['msg']['payload']['clientid'])
        ws_msg = {"type":"status.agent","msg":{"agent_id":msg['msg']['payload']['clientid'],"online":online,"reason":reason}}
        print("ws_msg", ws_msg)
        # ws = GlobalVar.get_ws_client()
        # await ws.send(json.dumps(ws_msg))
    elif msg['type'] == "usermonitor":
        online = True if msg["msg"]['status'] == "connected" else False
        reason = "" if msg["msg"]['status'] == "connected" else "program_exception" if msg['msg']['payload']['reason'] == "closed" else "network_exception"
        print(msg['msg']['payload']['broker_id'])
        ws_msg = {"type":"status.usermonitor","msg":{"broker_id":msg['msg']['payload']['broker_id'],"online":online,"reason":reason}}
        print("ws_msg", ws_msg)

    elif msg['type'] == "broker":
        ws_msg = {"type":"status.broker","msg":msg['msg']}
        print("broker ws_msg = ", ws_msg)

    elif msg['type'] == "app":
        ws_msg = {"type":"status.app","msg":msg['msg']}
        print("app ws_msg = ", ws_msg)
    elif msg['type'] == "container_log":
        ws_msg = {"type":"status.container_log","msg":msg['msg']}
    # TODO(gyf): test annotation
    elif msg['type'] == "con_cntr_ready":
        ws_msg = {"type":"status.con_cntr_ready","msg":msg['msg']}
    ws = GlobalVar.get_ws_client()
    await ws.send(json.dumps(ws_msg))
    # await send_msg(GlobalVar.get_ws_client(),ws_msg)

        
# 客户端主逻辑
async def main_logic():
    while True:
        try:
            msg = q.get()
            if msg != None:
                # print("msg type ", type(msg))
                # if 
                # jsonData = json.loads(msg)
                print(msg)
                if msg['comm'] == "ws":
                    print("msg come from websocket")
                    print("need enter websocket msg handler function")
                    await websocket_handler(msg['msg'])
                    # print("main thread websocket id ", id(GlobalVar.get_ws_client()))
                    # print("comm message is ",jsonData)
                    # await send_msg(GlobalVar.get_ws_client(),msg)
                if msg['comm'] == "mqtt":
                    print("msg come from mqtt")
                    print(" need enter mqtt msg handler function")
                    #TODO(gyf): controller得到mqtt消息后如何处理
                    await mqtt_handler(msg)

        except Exception as e:
            print("error is ", e)
            break

asyncio.get_event_loop().run_until_complete(main_logic())