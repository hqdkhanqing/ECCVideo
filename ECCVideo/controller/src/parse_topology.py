import sys
import ruamel.yaml
from ruamel.yaml.comments import CommentedMap      # CommentedMap用于解决ordereddict数据dump时带"!omap"这样的字段
from ruamel.yaml.scalarstring import SingleQuotedScalarString,DoubleQuotedScalarString
import logging
from pathlib import Path
import asyncio
import re
from utils import pub_msg
import globalvar as GlobalVar 
import json

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

yaml = ruamel.yaml.YAML()
yaml.preserve_quotes = True
yaml.indent(mapping=4, sequence=6, offset=4)

# def get_broker_id(broker_agents,agent_id):
#     for broker_agent in broker_agents:
#         if agent_id in broker_agent:
#             return broker_agent.split("/")[0]
# 连接信息配置转至orchestrator模块实现
# def connection2environment(container_name,connections,connect_index,broker_agents):
#     conn_dict = dict()
#     for connection in connections:
#         for key in connection.keys():
#             agent_id, conn_container_name, interface = connection[key].split("/")
#             if container_name == conn_container_name:
#                 if key == "from":
#                     # target_agent_id 用于查找目标设备的broker_id
#                     target_agent_id, target_conn_container_name, target_interface = connection["to"].split("/")
#                     target_agent_broker_id = get_broker_id(broker_agents,target_agent_id)
#                     conn_dict['CONNECT_{}'.format(connect_index)] = DoubleQuotedScalarString(dict(broker=target_agent_broker_id,interface=re.sub(r'(?:in|out)',target_conn_container_name,target_interface),type="pub"))
#                     connect_index += 1
#                 elif key == "to":
#                     # agent_id 用于查找本地broker_id
#                     local_agent_broker_id = get_broker_id(broker_agents,agent_id)
#                     conn_dict['CONNECT_{}'.format(connect_index)] = DoubleQuotedScalarString(dict(broker=local_agent_broker_id,interface=re.sub(r'(?:in|out)',conn_container_name,interface),type="sub"))
#                     connect_index += 1
#     logger.debug("conn_dict="+str(conn_dict))
#     return conn_dict



def parse_configuration(container):
    # TODO(gyf)：用于添加连接环境变量--------------------------
    connect_index = 0
    # conn_env = connection2environment(container['name'],connections,connect_index,broker_agent)
    #---------------------------------------------------------
    # container.pop("interfaces")
    container.pop("name")
    container.pop('agent')
    service = CommentedMap()
    service['environment'] = dict()
    for key,value in container.items():
        if key == "env":
            service['environment'].update(value)
        elif key == "resources":
            # compose version 2 资源限制
            for sub_key in container['resources']:
                service.update(container['resources'][sub_key])
            # compose version 3 资源限制
            # resource_dict = dict()
            # resource_dict["resources"] ={"limits":dict()}
            # for sub_key in container['resources']:
            #     resource_dict["resources"]["limits"].update(container["resources"][sub_key])
            # service['deploy'] = resource_dict
        else:
            service[key] = container[key]
    return service

# main 函数
async def parse_app_topology(msg):
    # app_topo = yaml.load(Path(file))
    # app_topo = yaml.load(physical_topology)
    logger.debug("type physical_topology="+str(type(msg['physical_topology'])))
    logger.debug("msg =="+str(msg))
    parser_type = "component"
    # TODO(gyf):测试注释
    if "parser_type" in msg:
        parser_type = msg["parser_type"]    # parser_type = controller/component
    
    logger.debug("parser_type="+str(parser_type))

    app_topo = msg['physical_topology']
    # connections = app_topo['connections']
    for agent_id in app_topo['agents']:
        out_name = 'agent-{}.yml'.format(agent_id)
        services = CommentedMap()   # 按顺序放，可用dict()，但是可能各service位置会改变
        # file_yml = CommentedMap(dict(version=DoubleQuotedScalarString("3.7"),services=services))
        file_yml = CommentedMap()
        # file_yml['version'] = DoubleQuotedScalarString("3.7")
        file_yml['version'] = DoubleQuotedScalarString("2.4")
        file_yml['services'] = services
        containers = app_topo['containers']
        logger.debug(str(type(containers)))
        logger.debug(str((containers)))
        match_index = []
        index = 0
        logger.debug("containers="+str(containers))
        for container in containers:
            service_name = f"edgeai_{msg['app_id']}_{container['name']}"
            # print(type(container))
            # container.insert(0,"container_name" , service_name)
            # container['container_name'] = service_name
            container.update({'container_name':service_name})
            logger.info(str(agent_id))
            # logger.debug("service_name="+service_name)
            if 'agent' in container and container['agent'] == agent_id and container["type"] == parser_type:
                logger.info(str(agent_id))
                services[service_name] = parse_configuration(container)
                logger.debug("add elem="+str(index))
                match_index.append(index)
                # containers.remove(container)
            index += 1
            # services.update({'container_name':service_name})

        # 若该agent下无container["type"] == parser_type 则直接跳过该agent
        if not match_index:
            continue

        logger.debug("match_index="+str(match_index))
        for index in sorted(match_index, reverse=True):
            del containers[index]
        path = Path("./data/"+msg['app_id']+"/"+out_name)
        try:
            if not path.parent.exists():
                path.parent.mkdir(parents=True)
        except Exception as e:
            logger.critical("path mkdir error is "+str(e))
        yaml.dump(file_yml, path)
        topic = 'toAgent/{}/{}/{}'.format(agent_id,"app","up")
        payload = {"app_id":msg['app_id'], "yml":json.dumps(file_yml),"compose_type":parser_type}
        logger.debug("pub topic="+str(topic))
        # logger.debug("pub topic="+str(payload))
    # TODO(gyf)  test temporary annotation---------------
        pub_msg(topic, json.dumps(payload))
    if parser_type == "component":
        logger.debug("controller return app success")
        from websocketComm import ws_send_msg
        ws = GlobalVar.get_ws_client()
        msg = {"type":"response.operation","msg":{"app_id":msg['app_id'],"operate":"up","success": True}}
        await ws_send_msg(ws,json.dumps(msg))
    # -------------------------------------------------------




def read_yml(file):
    with open(file,'r') as stream:
        logic_topo = yaml.load(stream)

    return logic_topo
# if __name__ == "__main__":
    # app_topology = read_yml('./app_topology.yml')
    # app_id = "app_id"
    # msg = {"app_id":app_id,"physical_topology":app_topology}
    # asyncio.get_event_loop().run_until_complete(parse_app_topology())
    # parse_app_topology(msg)