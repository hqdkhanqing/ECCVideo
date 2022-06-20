from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models import Q
import json
from .models import App, Orchestration, Broker, Agent, ContainerStatus, ContainerData, AgentData, BrokerMonitor, AppContainerLog
from channels.db import database_sync_to_async

class OrchestratorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Join room group
        await self.channel_layer.group_add(
            "orchestrator",
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            "orchestrator",
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        await self.channel_layer.group_send(
            "orchestrator",
            {
                'type': text_data_json['type'],
                'msg': text_data_json['msg']
            }
        )

    def update_physical_topology(self,id,physical_topology):
        try:
            app =  App.objects.get(pk=id)
            container_list = physical_topology['containers']
            ContainerStatus.objects.filter(app=app).delete()
            for container in container_list:
                container_name = container['name']
                agent_id = container['agent']
                agent = Agent.objects.get(pk=agent_id)
                container_type=container['type']
                ContainerStatus.objects.create(agent = agent,app = app, name = container_name, container_type=container_type)
            app.status = 1
            app.physical_topology = physical_topology
            app.save()
        except Exception as e:
            print('update_physical_topology error')
            print(e)
    
    # Receive message from room group
    async def update_app(self, event):
        app_id = event['msg']['app_id']
        physical_topology = json.loads(event['msg']['physical_topology'])
        print(app_id)
        print(physical_topology)
        await database_sync_to_async(self.update_physical_topology)(app_id,physical_topology)

    def get_logical_topology(self,id):
        try:
            logical_topology_file = App.objects.get(pk=id).logical_topology.file
            yaml_content = logical_topology_file.read().decode('utf-8')
            return yaml_content
        except Exception as e:
            print('get_logical_topology error')
            print(e)

    def get_map_info(self,id):
        orchestration = Orchestration.objects.filter(app=id).order_by('-commited_at')[0]
        map_info = orchestration.map_info
        return map_info

    # Receive message from room group, notifies the orchestrator of a new task
    async def orchestrate_app(self, event):
        try:
            app_id = event['msg']['app_id']
            logical_topology = await database_sync_to_async(self.get_logical_topology)(app_id)
            map_info = await database_sync_to_async(self.get_map_info)(app_id)
            map_list = map_info['maps']
            result_dict = {}
            for item in map_list:
                if 'agent' in item:
                    agent_id = item['agent']
                    agent = Agent.objects.get(pk=agent_id)
                    if agent.broker.mountpoint:
                        result_dict[agent_id] = {"is_cloud":agent.broker.is_cloud,"broker_id":str(agent.broker.id),"bridge_mountpoint":agent.broker.mountpoint}
                    else:
                        result_dict[agent_id] = {"is_cloud":agent.broker.is_cloud,"broker_id":str(agent.broker.id)}
                elif 'label' in item:
                    label_name = item['label']
                    result_dict[label_name] = dict()
                    agents = Agent.objects.filter(labels__contains="{"+label_name+"}")
                    for agent in agents:
                        if agent.broker.mountpoint:
                            result_dict[label_name][str(agent.id)] = {"is_cloud":agent.broker.is_cloud,"broker_id":str(agent.broker.id),"bridge_mountpoint":agent.broker.mountpoint}
                        else:
                            # print(label_name)
                            # print(str(agent.id))
                            # print(agent.broker.is_cloud)
                            # print(str(agent.broker.id))
                            result_dict[label_name][str(agent.id)] = {"is_cloud":agent.broker.is_cloud,"broker_id":str(agent.broker.id)}

            msg = {'app_id': app_id,'logical_topology':logical_topology,'map_info':map_info,'label_agent':result_dict}
            await self.send(text_data=json.dumps({
                'type': 'app_orchestrate',
                'msg': msg
            }))
        except Exception as e:
            print('orchestrate_app error')
            print(e)

class ControllerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Join room group
        await self.channel_layer.group_add(
            "controller",
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            "controller",
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        await self.channel_layer.group_send(
            "controller",
            {
                'type': text_data_json['type'],
                'msg': text_data_json['msg']
            }
        )

    def update_broker_status(self,id,online):
        try:
            broker =  Broker.objects.get(pk=id)
            if online:
                broker.status = 1
            else:
                broker.status = 0
            broker.save()
        except Exception as e:
            print('update_broker_status error')
            print(e)

    async def status_broker(self, event):
        broker_id = event['msg']['broker_id']
        online = event['msg']['online']
        await database_sync_to_async(self.update_broker_status)(broker_id,online)



    def update_monitor_status(self,id,online):
        try:
            brokerMonitor =  BrokerMonitor.objects.get(broker=id)
            if online:
                brokerMonitor.status = 1
            else:
                brokerMonitor.status = 0
            brokerMonitor.save()
        except Exception as e:
            print('update_monitor_status error')
            print(e)

    async def status_monitor(self, event):
        broker_id = event['msg']['broker_id']
        online = event['msg']['online']
        await database_sync_to_async(self.update_monitor_status)(broker_id,online)

    def update_agent_status(self,id,online):
        try:
            agent =  Agent.objects.get(pk=id)
            if online:
                agent.status = 1
            else:
                agent.status = 0
            agent.save()
        except Exception as e:
            print('update_agent_status error')
            print(e)

    async def status_agent(self, event):
        agent_id = event['msg']['agent_id']
        online = event['msg']['online']
        agent = Agent.objects.filter(pk=agent_id)
        print(agent)
        if len(agent) == 0:
            msg = {"operate":"operate.agent_delete", "agent_id": str(agent_id)}
            await self.send(text_data=json.dumps({
                    'type': "operate.agent_delete",
                    'msg': msg
                }))       
        else:
            await database_sync_to_async(self.update_agent_status)(agent_id,online)

    def update_container_status(self,agent_id,app_id,container_name,status):
        try:
            containerStatus = ContainerStatus.objects.get(Q(app=app_id) & Q(name=container_name))
            map_to_status = {
                'not-started':0,
                'running':1,
                'restarting':2,
                'paused':3,
                'exited':4,
                'created':5
            }
            if status != "running" or containerStatus.status != 6:
                containerStatus.status = map_to_status[status]
                containerStatus.save()
        except Exception as e:
            print('update_container_status error')
            print(e)

    async def status_app(self, event):
        print("=========status_app================")
        print(event)
        try:
            if isinstance(event['msg'],list):
                app_set = set()
                for item in event['msg']:
                    agent_id = item['agent_id']
                    app_id = item['app_id']
                    container_name = item['container_name']
                    status = item['status']
                    app =  App.objects.get(pk=app_id)
                    if app.status != 1:
                        await database_sync_to_async(self.update_container_status)(agent_id,app_id,container_name,status)
                    else:
                        app_set.add(app)
                for app_item in app_set:
                    msg = {'app_id': str(app_item.id),'physical_topology':app_item.physical_topology}
                    # Send message to WebSocket
                    await self.send(text_data=json.dumps({
                        'type': "operate.app_down",
                        'msg': msg
                    }))
        except Exception as e:
            print('status_app error')
            print(e)

    def update_app_status(self,id,operate,success):
        try:
            app =  App.objects.get(pk=id)
            map_to_status = {
                'up':2,
                'start':2,
                'stop':3,
                'down':1,
                'clean':1
            }
            if success:
                app.status = map_to_status[operate]
                if operate in ['down','clean']:
                    containerStatus_list = ContainerStatus.objects.filter(app=app)
                    for containerStatus_item in containerStatus_list:
                        containerStatus_item.status = 0
                        containerStatus_item.save()
            app.save()
        except Exception as e:
            print('update_app_status error')
            print(e)

    async def response_operation(self, event):
        app_id = event['msg']['app_id']
        operate = event['msg']['operate']
        success = event['msg']['success']
        await database_sync_to_async(self.update_app_status)(app_id,operate,success)

    def update_container_log(self,agent_id,app_id,container_name,log_info):
        try:
            timestamp = log_info['time'][0:-4].replace(' ','T')
            map_to_level = {
                'DEBUG':0,
                'INFO':1,
                'WARNING':2,
                'ERROR':3,
                'CRITICAL':4
            }
            level = map_to_level[log_info['level']]
            message = log_info['message']
            app=App.objects.get(pk=app_id)
            agent = Agent.objects.get(pk=agent_id)
            AppContainerLog.objects.create(agent=agent, app=app, container_name=container_name, \
                        timestamp = timestamp, level = level, message = message)
        except Exception as e:
            print('update_container_log error')
            print(e)

    async def status_container_log(self, event):
        app_id = event['msg']['app_id']
        container_name = event['msg']['container_name']
        log_info = event['msg']['log_info']
        agent_id = event['msg']['agent_id']
        await database_sync_to_async(self.update_container_log)(agent_id,app_id,container_name,log_info)

    def update_controller_container_status(self, agent_id,app_id,container_name,container_type):
        try:
            # app=App.objects.get(pk=app_id)
            # agent = Agent.objects.get(pk=agent_id)
            containerStatus = ContainerStatus.objects.get(Q(app=app_id) & Q(name=container_name) & Q(agent=agent_id) & Q(container_type=container_type))
            containerStatus.status = 6
            containerStatus.save()
        except Exception as e:
            print('update_controller_container_status error')
            print(e)



    # 新增controller应用容器的ready存储
    async def status_con_cntr_ready(self,event):
        app_id = event['msg']['app_id']
        container_name = event['msg']['container_name']
        agent_id = event['msg']['agent_id']
        container_type = event['msg']['container_type']
        if container_type == "controller":
            await database_sync_to_async(self.update_controller_container_status)(agent_id,app_id,container_name,container_type)



    # Receive message from room group
    async def operate_app(self, event):
        agent_list = event['msg']['physical_topology']['agents']
        # print("===event=====")
        print(str(event))
        msg = {'app_id': event['msg']['app_id'],'physical_topology':event['msg']['physical_topology']}
        if event['msg']['operate'] in ["operate.app_up","operate.app_start"]:
            msg.update({"parser_type":event['msg']['parser_type']})

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': event['msg']['operate'],
            'msg': msg
        }))

    async def operate_agent(self, event):
        msg = {'agent_id': event['msg']['agent_id']}
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': event['msg']['operate'],
            'msg': msg
        }))

class MonitorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Join room group
        await self.channel_layer.group_add(
            "monitor",
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            "monitor",
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        print(text_data_json)
        await self.channel_layer.group_send(
            "monitor",
            {
                'type': text_data_json['type'],
                'msg': text_data_json['msg']
            }
        )

    def update_monitor_data(self,app_info,agent_info):
        print('------------------------monitor-----------------------')
        print(app_info)
        print(agent_info)
        try:
            agent_id = agent_info['device']
            agent_cpu_count = agent_info['cpu_count']
            agent_cpu_usage = agent_info['cpu_usage']
            agent_mem_size = agent_info['mem_size']
            agent_mem_usage = agent_info['mem_usage']
            agent_net_in = agent_info['net_in']
            agent_net_out = agent_info['net_out']
            agent_timestamp = agent_info['timestamp']
            agent = Agent.objects.get(pk=agent_id)
            AgentData.objects.create(agent=agent, cpu_count=agent_cpu_count, cpu_usage = agent_cpu_usage, mem_size = agent_mem_size, \
                    mem_usage = agent_mem_usage, net_in = agent_net_in, net_out = agent_net_out, timestamp = agent_timestamp)
            for container_info in app_info:
                container_name = container_info['container_name']
                container_app_id = container_info['app']
                container_app = App.objects.get(pk=container_app_id)
                container_agent_id = container_info['device']
                container_agent = Agent.objects.get(pk=container_agent_id)
                container_mem_usage = container_info['mem_usage']
                container_mem_percent = container_info['mem_percent']
                container_net_in = container_info['net_in']
                container_net_out = container_info['net_out']
                container_cpu_usage = container_info['cpu_usage']
                container_timestamp = container_info['timestamp']
                container_image_name = container_info['image_name']
                container_status = container_info['status']
                container_create_at = container_info['create_at']
                container_platform = container_info['platform']
                ContainerData.objects.create(agent=container_agent, app=container_app, container_name=container_name, cpu_usage = container_cpu_usage, image_name = container_image_name, \
                        mem_usage = container_mem_usage, mem_percent = container_mem_percent, net_in = container_net_in, net_out = container_net_out, timestamp = container_timestamp, status=container_status, \
                            create_at = container_create_at, platform = container_platform)
        except Exception as e:
            print('update_monitor_data error')
            print(e)

    async def monitor_data(self, event):
        print('------------------monitor.data-------------------')
        agent_id = event['msg']['agent_id']
        app_info = event['msg']['app']
        agent_info = event['msg']['agent']
        agent =  Agent.objects.filter(pk=agent_id)
        print(agent)
        msg = {"operate":"operate.agent_delete", "agent_id": str(agent_id)}
        if len(agent) == 0:
            await self.send(text_data=json.dumps({
                    'type': "operate.agent_delete",
                    'msg': msg
                }))
        else:
            await database_sync_to_async(self.update_monitor_data)(app_info, agent_info)
