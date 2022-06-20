import paho.mqtt.client as mqtt
import os
import re
import asyncio
import json
import globalvar as GlobalVar 

async def distribute_to_agent(resource,type_id,operate,agents=None,compose_type=None):
    # resource 为app/agent  type_id 为app_id/agent_id   operate见websocket_handler function， agents 在处理应用时不为None
    print("-----agents----",agents)
    if agents == None:
        topic = 'toAgent/{}/{}/{}'.format(type_id,resource,operate)
        payload = {"app_id":type_id}
        print('---------------------agent------------------')
        print(topic)
        print(payload)
        pub_msg(topic, json.dumps(payload))
    else:
        for agent_id in agents:
            topic = 'toAgent/{}/{}/{}'.format(agent_id,resource,operate)
            if operate == "start":
                payload = {"app_id":type_id,"compose_type":compose_type}
            else:
                payload = {"app_id":type_id}
            # payload = {"app_id":type_id}
            print('---------------------app------------------')
            print(topic)
            print(payload)
            pub_msg(topic, json.dumps(payload))
        # start和up时，只有为component才send success
        if operate == "start" and  compose_type == "controller":
            pass
        elif operate == "delete":
            pass
        else:
            ws = GlobalVar.get_ws_client()
            msg = {"type":"response.operation","msg":{"app_id":type_id,"operate":operate,"success": True}}
            await ws.send(json.dumps(msg))
    # for dirpath,dirnames,filenames in os.walk("./data/"+app_id):
    #     for file in filenames:
    #         fullpath = os.path.join(dirpath,file)
    #         # topic = 'toAgent/'+re.findall('device-(.*).yml', fullpath)[0]+'/app/create'
    #         topic = 'toAgent/{}/{}/{}'.format(re.findall('device-(.*).yml', fullpath)[0],resource,operate)
    #         payload = {}
    #         payload['app_id'] = app_id
    #         if operate == "up":
    #             with open(fullpath,'r') as f:
    #                 ymlcontent = f.read()
    #             payload['yml'] = ymlcontent
    #         pub_msg(topic,payload)


def pub_msg(topic, payload, qos=2):
    print("pub_msg")
    client = GlobalVar.get_mq_client()
    client.publish(topic, str(payload), qos)