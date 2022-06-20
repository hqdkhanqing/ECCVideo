import logging
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import json
import ast
import os

class MQTTHandler(logging.Handler):
    def __init__(self,
                 hostname,
                 port,
                 broker_id,
                 app_id,
                 container_name,
                 agent_id,
                 qos=2,
                 retain=False,
                 keepalive=60,
                 will=None,
                 auth=None,
                 tls=None,
                 protocol=mqtt.MQTTv31,
                 transport='tcp',
                 pre_topic="toEdgeAI"):
        logging.Handler.__init__(self)
        self._hostname = hostname
        self._port = port
        self._broker_id = broker_id
        self._app_id = app_id
        self._container_name = container_name
        self._agent_id = agent_id
        self._qos = qos
        self._retain = retain
        self._keepalive = keepalive
        self._will = will
        self._auth = auth
        self._tls = tls
        self._protocol = protocol
        self._transport = transport
        self._pre_topic = pre_topic
        self.formatter = logging.Formatter("{'time':'%(asctime)s','name':'%(name)s','level':'%(levelname)s','message':'%(message)s'}")

    def emit(self, record):
        """
        Publish a single formatted logging record to a broker, then disconnect
        cleanly.
        """
        msg = self.format(record)
        msg = ast.literal_eval(msg)
        print(type(msg))
        print(msg)
        payload = {"app_id":self._app_id, "container_name":self._container_name, "agent_id":self._agent_id, "log_info":msg}
        json_payload  = json.dumps(payload)
        print(f"{self._pre_topic}/{self._broker_id}/log")
        publish.single(f"{self._pre_topic}/{self._broker_id}/log",
                       json_payload,
                       self._qos,
                       self._retain,
                       hostname=self._hostname,
                       port=self._port,
                       client_id=self._app_id,
                       keepalive=self._keepalive,
                       will=self._will,
                       auth=self._auth,
                       tls=self._tls,
                       protocol=self._protocol,
                       transport=self._transport)


class Logger:
    def __init__(self,hostname,port,broker_id,app_id,container_name,agent_id):
        self._hostname = hostname
        self._port = port  
        self._brokere_id = broker_id
        self._app_id = app_id
        self._container_name = container_name
        self._agent_id = agent_id

        #TODO(gyf)：后续这些参数应该都是直接从环境变量获取而不是人为设定
        # self._hostname = os.getenv("ECCI_LOCAL_BROKER_IP")
        # self._port = os.getenv("ECCI_LOCAL_BROKER_PORT")  
        # self._brokere_id = os.getenv("ECCI_LOCAL_BROKER_ID")
        # self._app_id = os.getenv("ECCI_APP_ID")
        # self._container_name = os.getenv("ECCI_CONTAINER_NAME")
        # self._agent_id = os.getenv("ECCI_AGENT_ID")
    def initialize(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        mqttHandler = MQTTHandler(self._hostname, self._port, self._brokere_id, self._app_id, self._container_name, self._agent_id)
        # mqttHandler.setLevel(logging.NOTSET)
        logger.addHandler(mqttHandler)
        return logger
