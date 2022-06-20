# logger.py
logger.py 是对logger上Handler的扩展，将日志信息通过MQTT发送到ECCI系统中。

## 作用
用于在其上开发的应用提供将应用容器中的`日志信息`传入ECCI系统

## 日志信息流程
1. 应用容器将日志信息发送到其边缘云上的broker
2. 边缘云端Broker Monitor采集到该信息，经过初部解析将其发给ECCI broker
3. Controller 订阅到该消息后经过处理发送到api-server进行存储

## 使用方式
```
from logger import Logger
logger = Logger("edgecloud_broker_ip",edgecloud_broker_port,"pre_topic 后续可能将其强制指定","broker_id","app_id","container_name")

logger = logger.initialize()
logger.debug("a debug message")
logger.info("an info message")
logger.warning("a warning message")
logger.error("an error message")
logger.critical("a critical message")

```
## 订阅输出结果
```
topic=testMQTTLogging/broker_id
msg type=<class 'bytes'>
msg = b'{"app_id": "app_id", "container_name": "contaiiner_name", "log_info": {"time": "2020-02-17 11:17:22,826", "name": "testMqttHandlerClass", "level": "DEBUG", "message": "a debug message"}}'

topic=testMQTTLogging/broker_id
msg type=<class 'bytes'>
msg = b'{"app_id": "app_id", "container_name": "contaiiner_name", "log_info": {"time": "2020-02-17 11:17:22,830", "name": "testMqttHandlerClass", "level": "INFO", "message": "an info message"}}'

topic=testMQTTLogging/broker_id
msg type=<class 'bytes'>
msg = b'{"app_id": "app_id", "container_name": "contaiiner_name", "log_info": {"time": "2020-02-17 11:17:22,832", "name": "testMqttHandlerClass", "level": "WARNING", "message": "a warning message"}}'

topic=testMQTTLogging/broker_id
msg type=<class 'bytes'>
msg = b'{"app_id": "app_id", "container_name": "contaiiner_name", "log_info": {"time": "2020-02-17 11:17:22,834", "name": "testMqttHandlerClass", "level": "ERROR", "message": "an error message"}}'

topic=testMQTTLogging/broker_id
msg type=<class 'bytes'>
msg = b'{"app_id": "app_id", "container_name": "contaiiner_name", "log_info": {"time": "2020-02-17 11:17:22,836", "name": "testMqttHandlerClass", "level": "CRITICAL", "message": "a critical message"}}'
```

# ecci_client.py
ecci_client.py 是ecci提供的关于mqtt、文件通信的接口。

## 作用
自动提供topic的解析、队列存储消息等；mqtt通信及文件通信方式

## 文件发送端示例代码
```
from ecci_sdk import Client
import logging
import threading

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

ecci_client = Client()
ecci_client.initialize()

filepath = r'./test.py'
filename = 'test'

def transfer():
    while True:
        if filename in ecci_client.get_sub_put_file_dict() :
            ecci_client.transfer(filename,'containerB')
            while not ecci_client.get_sub_put_file_dict()[filename]['is_transfered']:
                pass
            return 

def puturl():
    # 选择文件传输
    ecci_client.putHandler(filename,'containerB',filepath=filepath)

    # 数据以文件方式传输
    # ecci_client.putHandler(filename,'containerB',contents=['2','33'])

if __name__ == "__main__":
    thread_transfer = threading.Thread(target=transfer)
    thread_puturl = threading.Thread(target=puturl)
    thread_transfer.start()
    thread_puturl.start()
    thread_puturl.join()
    thread_transfer.join()
```

## 文件接收端示例代码
```
from ecci_sdk import Client
import logging
import threading

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

ecci_client = Client()
ecci_client.initialize()

filename = 'test'
filepath = '/test.py'

if __name__ == "__main__":
    while True:
        if filename in ecci_client.get_sub_get_file_dict():
            # 下载contents类型并反序列化
            # print(ecci_client.download_contents(ecci_client.get_sub_get_file_dict()[filename]))

            # 下载文件类型
            ecci_client.download_file(filepath, ecci_client.get_sub_get_file_dict()[filename])
            break
```