
from wscomm import ws_send
import logging
from threading import Thread
# from wscomm import ws_main
# from mqttcomm import mq_main
import os

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from mqttcomm import mqtt_send

ECCI_MONITOR_MODE = os.getenv("ECCI_MONITOR_MODE")

class routing(object):
    def __init__(self, message):
        self.message = message
        func_dict = {"system": self.websocket, "user": self.mqtt}
        self.routing_func = func_dict.get(ECCI_MONITOR_MODE, self.func_None)
    
    def mqtt(self):
        print('user monitor, routing mqtt msg')
        return mqtt_send(self.message)
 
    def websocket(self):
        print('system monitor, routing websocket msg')
        return ws_send(self.message)
    
    def func_None(self):
        print('mode of monitor is not supported')

# class forwarding(object):
#     def __init__(self,conf,comm_queue):
#         self.comm_queue = comm_queue
#         self.conf = conf
#         func_dict = {"system":self.system_comm_init, "user":self.user_comm_init}
#         self.forwarding_func = func_dict.get(conf['mode'],self.func_None)
    
#     def system_comm_init(self):
#         logger.info("create system monitor related client")
#         sub_listen = Thread(target=mq_main,args=(self.comm_queue,))
#         sub_listen.start()

#         forward_listen = Thread(target=ws_main)
#         forward_listen.start()

        

#     def user_comm_init(self):
#         logger.info("create user monitor related client")
#         sub_listen = Thread(target=mq_main,args=(self.comm_queue,))
#         sub_listen.start()

#         forward_listen = Thread(target=mq_main)
#         forward_listen.start()
        
        
    
#     def func_None(self):
#         logger.critical("Unknown mode ",conf['mode'])
    
    
