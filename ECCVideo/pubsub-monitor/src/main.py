from threading import Thread
import queue
from wscomm import ws_forward_main
from mqttcomm import mq_sub_main,mq_forward_main
import globalvar as GlobalVar 
import time
import asyncio
import json
import re
import os
import logging
from routing import routing
# from utils import get_conf

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

q = queue.Queue()

ECCI_MONITOR_MODE = os.getenv("ECCI_MONITOR_MODE",default="system")

if ECCI_MONITOR_MODE == "system":
    forward_listen = Thread(target=ws_forward_main)
    forward_listen.start()
elif ECCI_MONITOR_MODE == "user":
    forward_listen = Thread(target=mq_forward_main)
    forward_listen.start()


sub_listen = Thread(target=mq_sub_main,args=(q,))
sub_listen.start()

# 向服务器端发送认证后的消息
async def send_msg(websocket,msg):
    print("type msg ", type(msg))
    print("msg ", msg)
    send_text = json.dumps(msg)
    print("before websocket.send")
    await websocket.send(send_text)



async def route_func(msg):
    # ws = GlobalVar.get_forward_client()
    # conf = get_conf("monitor","destination")
    if ECCI_MONITOR_MODE == "user":
        routing(msg).routing_func()
    elif ECCI_MONITOR_MODE == "system":
        await routing(msg).routing_func()
    # await ws.send(json.dumps(msg))
        
# 客户端主逻辑
async def main_logic():
    while True:
        try:
            msg = q.get()
            if msg != None:
                print("msg come from mqtt")
                print(" need enter mqtt msg handler function")
                #TODO(gyf): controller得到mqtt消息后如何处理
                print(msg)
                await route_func(msg)

        except Exception as e:
            print("error is ", e)
            break

asyncio.get_event_loop().run_until_complete(main_logic())