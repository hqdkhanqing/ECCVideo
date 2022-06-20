import ruamel.yaml
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.scalarstring import DoubleQuotedScalarString
import logging
import json
import copy
import ast

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

yaml = ruamel.yaml.YAML()
yaml.preserve_quotes = True
yaml.indent(mapping=4, sequence=6, offset=4)

# def agent_match(containers, orchestrate_info,orche_policy):
#     if orche_policy == "direct":
#         agents = set()
#         for container in containers:
#             for dev_container_map in orchestrate_info:
#                 if dev_container_map["container"] == container['name']:
#                     container["agent"] = dev_container_map['agent']
#                     agents.add(dev_container_map['agent'])
#                     break
#             if "agent" not in container:
#                 logger.critical("存在容器没有匹配到设备")
#     else:
#         logger.info("need complete")
#     return list(agents)

# def container_agents_combination(container,agents_label):
#     label_containers = list()
#     name_prefix = container['name']
#     for index,agent in enumerate(agents_label.keys()):
#         container['name'] = f"{name_prefix}_{index}"
#         container['agent'] = {agent:copy.deepcopy(agents_label[agent])}
#         label_containers.append(copy.deepcopy(container))
#     return label_containers

def add_container_location_env(container):
    if "env" not in container:
        container['env'] = dict()
    container_location = "cloud" if list(container['agent'].values())[0]["is_cloud"] else "edge"
    container['env'].update({"ECCI_CONTAINER_TYPE":container_location})

# 给每个container中新增agent键值对，包含该agent和其一些必要的信息
def agent_match(containers, orchestrate_info,label_agent):
    agents = set()
    # label_containers = list()
    # wait_delete_container = list()
    for dev_container_map in orchestrate_info:
        for container in containers:
            if dev_container_map['container'] == container['name']:
                if 'agent' in dev_container_map:
                    container['agent'] = {dev_container_map['agent']:copy.deepcopy(label_agent[dev_container_map['agent']])}
                    agents.add(dev_container_map['agent'])
                    break
                else:
                    logger.critical(f"{dev_container_map['container']} has no corresponding agent")
                # elif 'label' in dev_container_map:
                #     if dev_container_map['label'] not in label_agent:
                #         logger.critical(f"label_agent中没有标签{dev_container_map['label']}对应的设备组")
                #     else:
                #         agents_label = label_agent[dev_container_map['label']]
                #         # 去除标签——即pop取出该标签下的agents,然后再update回pop后的字典中
                #         # agents_label = label_agent.pop(dev_container_map['label'])
                #         # label_agent.update(agents_label)
                #         agents.update(agents_label.keys())
                #         wait_delete_container.append(index)
                #         label_containers.extend(container_agents_combination(container,agents_label))
            else:
                logger.critical(f"The orchestration container {dev_container_map['container']} is not in the containers {containers}")
    # for index in sorted(wait_delete_container,reverse=True):
    #     del containers[index]
    # containers.extend(label_containers)  

    return list(agents)


# def connections_add_agent_info(connections,container_agent_maps):
#     for container_agent_map in container_agent_maps:
#         print(container_agent_map)
#         for connection in connections:
#             print(connection)
#             for key in connection.keys():
#                 container_name = connection[key].split('/')[0]
#                 if container_name == container_agent_map['container']:
#                     print("match container "+container_name)
#                     print(container_agent_map['agent'])
#                     connection[key] = container_agent_map['agent']+"/"+connection[key]
#                     print(connection[key])
#                     print(connections)
def add_pub_targets_env(container, pub_targets_env):
    if 'env' not in container:
        container['env'] = dict()
    container['env'].update({"ECCI_PUB_TARGETS":DoubleQuotedScalarString(pub_targets_env)})

# 添加ECCI_APP_CONTROLLER_CONTAINER用于应用容器(component/controller)发送就绪给控制器(controller)
def add_app_controller_container(container, app_controller_container):
    if 'env' not in container:
        container['env'] = dict()
    if app_controller_container:
        container['env'].update({"ECCI_APP_CONTROLLER_CONTAINER":DoubleQuotedScalarString(app_controller_container)})


def add_bridge_mountpoint_env(container, bridge_mountpoint):
    if 'env' not in container:
        container['env'] = dict()
        # container['env'].update({"ECCI_BRIDGE_MOUNTPOINTS":list()})
    container_env = container['env']
    if "ECCI_BRIDGE_MOUNTPOINTS" not in container_env:
        container_env["ECCI_BRIDGE_MOUNTPOINTS"] = DoubleQuotedScalarString([bridge_mountpoint])
    else:
        bridge_mountpoints = set(ast.literal_eval(container_env["ECCI_BRIDGE_MOUNTPOINTS"]))
        print("type(bridge_mountpoints)=",type(bridge_mountpoints))
        bridge_mountpoints.add(bridge_mountpoint)
        container_env["ECCI_BRIDGE_MOUNTPOINTS"] = DoubleQuotedScalarString(list(bridge_mountpoints))
    # pass

def get_container_name_index_map(container):
    index, container = container
    return container['name'], index

def agents_add_sys_env(containers, connections):
    print(type(containers))
    # 获取每个容器对应其列表中的位置{container_name：index}
    container_name_index_map = dict(map(get_container_name_index_map,enumerate(containers)))
    print("container_name_index_map=",container_name_index_map)
    # for container in containers:
    #     container_name = container['name']
    #     for pub_name in connections.keys():
    #         # 找到container当前需要发送的目标容器，更新ECCI_PUB_TARGETS
    #         if container_name.startswith(pub_name):
    #             # add_pub_targets_env(container,connections[pub_name])
    #             source_info = list(container['agent'].values())[0]
    #             if "bridge_mountpoint" in source_info:
    #                 bridge_mountpoint = source_info['bridge_mountpoint']
    #             cur_container_targets = connections[pub_name]
    #             pub_targets_env_dict = dict()
    #             for pub_container_name in cur_container_targets:

    for container in containers:
        source_container_name = container['name']
        # 获取以container_name为前缀发送目的地容器cur_container_pub_targets
        for pub_name in connections.keys():
            if source_container_name == pub_name:
                # 源agent信息
                source_info = list(container['agent'].values())[0]

                source_container_type = containers[container_name_index_map[source_container_name]]['type']
                # # source_info = list(containers[container_name_index_map])
                # if "bridge_mountpoint" in source_info:
                #     bridge_mountpoint = source_info['bridge_mountpoint']
                cur_container_pub_targets = connections[pub_name]

                # TODO(gyf): direct 类型不存在一个controller 监控多个同组应用component,即mode_train不存在mode_train_n，该部分在label 策略中存在
                # if source_container_type == "controller":

                pub_targets_env_dict = dict()

                # 遍历每个目的地容器
                for pub_container_name in cur_container_pub_targets:
                    app_controller_container = dict()
                    # 匹配到相应目的地容器
                    for destination_container_name in container_name_index_map.keys():
                        if destination_container_name == pub_container_name:
                            # print("containers=",containers)
                            destination_info = list(containers[container_name_index_map[destination_container_name]]['agent'].values())[0]
                            
                            if source_container_type == "controller":
                                app_controller_container = {source_container_name:source_info['broker_id']}
                            print("source_info=",source_info)
                            print("destination_info=",destination_info)
                            if source_info['is_cloud'] == "false" and destination_info['is_cloud'] == "false" and source_info['broker_id'] != destination_info['broker_id']:
                                logger.info("Both sender and receiver are edge clouds, so they cannot be sent, so they are not added to pub_targets")
                            else:
                                pub_target = {destination_container_name:destination_info['broker_id']}
                                pub_targets_env_dict.update(pub_target)
                            # print("source_info=",source_info)
                            if "bridge_mountpoint" in source_info and source_info['broker_id'] != destination_info['broker_id'] and source_info['is_cloud'] != destination_info['is_cloud']:
                                add_bridge_mountpoint_env(containers[container_name_index_map[destination_container_name]], source_info['bridge_mountpoint'])
                            # 添加controller对其他container的桥接信息sub
                            if source_container_type == "controller" and "bridge_mountpoint" in destination_info and source_info['broker_id'] != destination_info['broker_id'] and source_info['is_cloud'] != destination_info['is_cloud']:
                                add_bridge_mountpoint_env(containers[container_name_index_map[source_container_name]], destination_info['bridge_mountpoint'])
                            add_app_controller_container(containers[container_name_index_map[destination_container_name]], app_controller_container)
                print("pub_targets_env_dict=",pub_targets_env_dict)
                print("source_info=",source_info)
                print("destination_info=",destination_info)
                add_pub_targets_env(containers[container_name_index_map[source_container_name]], pub_targets_env_dict)
    for container in containers:
        add_container_location_env(container)
        container['agent'] = list(container['agent'].keys())[0]

def direct_func(logical_topology, map_info, label_agent):

    logical_topology = yaml.load(logical_topology)

    app_topo = CommentedMap()
    app_topo['appname'] = logical_topology['Logical_topolopy']

    # payload_info = map_info
    containers = logical_topology['containers']

    connections = logical_topology["connections"]

    agents = agent_match(containers, map_info['maps'], label_agent)

    agents_add_sys_env(containers,connections)
    
    # logger.debug("logic_topo[connections]="+str(logic_topo["connections"]))
    # connections_add_agent_info(logic_topo["connections"],payload_info['maps'])
    # app_topo["connections"] = logic_topo["connections"]
    # app_topo["agents"] = agents

    app_topo['containers'] = containers
    app_topo["connections"] = connections
    app_topo["agents"] = agents

    from pathlib import Path
    path = Path('./physical_topology_direct.yml')
    yaml.dump(app_topo,path)

    output = json.dumps(app_topo)
    return output
