import os
import configparser
# from wscomm import ws_send
# from mqttcomm import mq_send
import asyncio

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

CONFIG_FILE = "../config.conf"

# def config_ini():
#     print("config_ini")
#     if not os.path.exists(CONFIG_FILE):
#         logger.info("create a new profile")
#         # os.makedirs(CONFIG_FILE)
#         cf = configparser.ConfigParser()
#         cf.read(CONFIG_FILE)
#         cf.add_section("monitor")
#         cf.set("monitor","mode","")

#         cf.add_section("source")
#         cf.set("source","ip", "")
#         cf.set("source","port","")
#         cf.set("source","topic","")
#         cf.set("source","username","")
#         cf.set("source","password","")

        
#         cf.add_section("destination")
#         cf.set("destination","ip","")
#         cf.set("destination","port","")
#         cf.set("destination","url","")
#         cf.set("destination","username","")
#         cf.set("destination","password","")

#         cf.write(open(CONFIG_FILE, "w"))

# def monitor_ini(args):
#     cf = configparser.ConfigParser()
#     cf.read(CONFIG_FILE)
#     if args.module == "sys":

#         cf.set("monitor","mode","system")

#         cf.set("source","ip","10.0.3.99")
#         cf.set("source","port","1883")
#         cf.set("source","topic","toEdgeAI/monitor/#")
#         cf.set("source","username","admin")
#         cf.set("source","password","admin123")

#         cf.set("destination","ip","10.0.3.99")
#         cf.set("destination","port","8000")
#         cf.set("destination","url","monitor")
#         cf.set("destination","username","admin")
#         cf.set("destination","password","admin123")

#         cf.write(open(CONFIG_FILE, "w"))

#     elif args.module == "user":
#         cf.set("monitor","mode","user")

#         cf.set("source","ip","localhost")
#         cf.set("source","port","1883")
#         cf.set("source","topic","$SYS/brokers/edgeai@39.99.146.169/")
#         cf.set("source","username","admin")
#         cf.set("source","password","admin123")

#         cf.set("destination","ip","39.99.146.169")
#         cf.set("destination","port","1883")
#         cf.set("destination","url","toEdgeAI/")
#         cf.set("destination","username","admin")
#         cf.set("destination","password","admin123")

#         cf.write(open(CONFIG_FILE, "w"))

# def get_conf(*args):
#     cf = configparser.ConfigParser()
#     cf.read(CONFIG_FILE)
#     confs = {}
#     for section in args:
#         confs.update(cf._sections[section])
#     # print(confs)
#     return confs

# async def send_msg(msg,pattern=None,mold=None):
#     conf = get_conf("destination","monitor")
#     msg_type = "{}.{}".format(pattern,mold)
#     msg['type'] = msg_type
#     if conf['mode'] == "system":
#         await ws_send(msg,conf)
#     elif conf['mode'] == "user":
#         mq_send(msg,conf,mold)
#         print("send mqtt for EdgeAI")