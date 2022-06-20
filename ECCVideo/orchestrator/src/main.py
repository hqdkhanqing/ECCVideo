import asyncio
import websockets
import json
import os
import ruamel.yaml
from orchestration import orchestration
from ruamel.yaml.comments import CommentedMap   

yaml = ruamel.yaml.YAML()
yaml.preserve_quotes = True
yaml.indent(mapping=4, sequence=6, offset=4)

# ECCI_WEBSOCKET_PORT = os.getenv("ECCI_WEBSOCKET_PORT",default="8000")

# TODO(gyf) opt annotation
async def orchestrate(websocket, orchestrating_data):
    # map_info = recv_msg['map_info']
    # logical_topology = recv_msg['logical_topology']
    physical_topology = orchestration(orchestrating_data).orchestrate_func()
    send_text = json.dumps({'type':'update_app', \
        'msg':{'app_id':orchestrating_data['app_id'], 'physical_topology':physical_topology}})
    await websocket.send(send_text)

# async def orchestrate(orchestrating_data):
#     physical_topology = orchestration(orchestrating_data).orchestrate_func()
#     send_text = json.dumps({'type':'update_app', \
#         'msg':{'app_id':orchestrating_data['app_id'], 'physical_topology':physical_topology}})
#     await websocket.send(send_text)
    
#-------------------------------------------------------------------
# TODO(gyf) opt temporary annotation
async def recv_msg(websocket):
    while True:
        recv_text = json.loads(await websocket.recv())
        print(f"{recv_text}")
        print(recv_text['type'])
        if recv_text['type'] == 'app_orchestrate':
            # map_info = recv_text['msg']['map_info']
            # logical_topology = recv_text['msg']['logical_topology']
            await orchestrate(websocket, recv_text['msg'])

async def main_logic():
    ECCI_ORCHESTRATOR_WS_IP = os.getenv("ECCI_ORCHESTRATOR_WS_IP","api-server")
    ECCI_ORCHESTRATOR_WS_PORT = int(os.getenv("ECCI_ORCHESTRATOR_WS_PORT",8000))
    async with websockets.connect(f"ws://{ECCI_ORCHESTRATOR_WS_IP}:{ECCI_ORCHESTRATOR_WS_PORT}/ws/orchestrator/") as websocket:
        await recv_msg(websocket)

asyncio.get_event_loop().run_until_complete(main_logic())
#-------------------------------------------------------------------

# TODO(gyf):  临时测试实验
# import json
# def payload_simulate(filename):
#     with open(filename,'r') as tmp:
#         data = json.load(tmp)
#     return data

# def read_yml(file):
#     with open(file,'r') as stream:
#         logic_topo = yaml.load(stream)

#     return logic_topo
# async def main_logic():
#     # label-policy---------------------------------
#     # logic_topo = read_yml('./logic_topology.yml')
#     # map_info = payload_simulate('./orchestrate_info.json')
#     # label_agent = payload_simulate('./label_agent.json')
#     # label-policy---------------------------------
#     # direct-policy--------------------------------
#     # logic_topo = read_yml('./logic_topology_direct.yml')
#     # map_info = payload_simulate('./orchestrate_info_direct.json')
#     # label_agent = payload_simulate('./label_agent_direct.json')
#     # direct-policy--------------------------------
#     logic_topo_json = json.dumps(logic_topo)
#     logic_topo_dict = json.loads(logic_topo_json)
#     print(type(logic_topo))
#     print(type(logic_topo_json))
#     print(type(logic_topo_dict))
#     print(type(map_info))
#     print(type(label_agent))
#     orchestrating_data = {"map_info":map_info,"logical_topology":logic_topo_dict,"label_agent":label_agent}
#     await orchestrate(orchestrating_data)

asyncio.get_event_loop().run_until_complete(main_logic())