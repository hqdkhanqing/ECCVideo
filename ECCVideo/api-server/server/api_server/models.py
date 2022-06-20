from django.db import models
import jsonfield
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils.timezone import timedelta
import uuid, os, json, re, yaml
from channels.layers import get_channel_layer

from asgiref.sync import async_to_sync

from django.db.models import Q

class User(AbstractUser):
    """
    An abstract base class implementing a fully featured User model with
    admin-compliant permissions.
 
    """
    jwt_secret = models.UUIDField(default=uuid.uuid4)
    # jwt_secret = models.CharField(max_length=100, default=shortuuid.uuid)
    salt = models.CharField(max_length=100, null=True, default='default_salt')

    def __str__(self):
        return self.username

def jwt_get_secret_key(user):
    return user.jwt_secret


class Registry(models.Model):
    id = models.CharField(primary_key=True, max_length=25, editable=False)
    # id = models.UUIDField(primary_key=True, default=uuid.uuid1, editable=False)
    name = models.CharField(max_length=100, null=False)
    description = models.CharField(max_length=255,null=True)
    ip_port = models.CharField(max_length=30,null=False)
    status_list = (
        (0, '离线'), 
        (1, '健康')
    )
    status = models.IntegerField(choices=status_list, null=False, default=0)
    def __str__(self):
        return self.name

class MqttACL(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid1, editable=False)
    allow = models.IntegerField(choices=((0,'禁止'),(1,'允许')), null=False, default=0)
    ipaddr = models.CharField(max_length=60, null=True)
    username = models.CharField(max_length=100, null=True)
    clientid = models.CharField(max_length=100, null=True)
    access = models.IntegerField(choices=((1,'仅能订阅'),(2,'仅能发布'),(3, '订阅/发布')), null=False, default=3)
    topic = models.CharField(max_length=100,null=False)

    def __str__(self):
        return self.clientid

class Broker(models.Model):
    id = models.CharField(primary_key=True, max_length=25, editable=False)
    # id = models.UUIDField(primary_key=True, default=uuid.uuid1, editable=False)
    is_cloud = models.BooleanField(null=False,default=False)
    name = models.CharField(max_length=100, null=False, unique=True)
    description = models.CharField(max_length=255,null=True)
    ip = models.GenericIPAddressField(max_length=15,null=False)
    port = models.IntegerField(null=False)
    mountpoint = models.CharField(max_length=20,null=True)
    status_list = (
        (0, '离线'), 
        (1, '健康')
    )
    status = models.IntegerField(choices=status_list, null=False, default=0)
    registrant = models.ForeignKey(
        User,
        editable=False,
        null=False,
        on_delete=models.CASCADE,
        related_name='broker_registrant')
    registered_at = models.DateTimeField(auto_now_add=True, editable=False)
    def __str__(self):
        return self.name

@receiver(post_save, sender=Broker)
def add_broker_monitor(sender, instance, signal, *args, **kwargs):
    if sender is Broker:
        broker_id = instance.id
        broker = Broker.objects.get(pk=broker_id)
        BrokerMonitor.objects.create(broker = broker)
    else:
        pass

class BrokerMonitor(models.Model):
    broker = models.ForeignKey(
        Broker,
        editable=False,
        null=False,
        on_delete=models.CASCADE,
        related_name='monitor_broker')
    status_list = (
        (0, '离线'), 
        (1, '健康')
    )
    status = models.IntegerField(choices=status_list, null=False, default=0)
    def __str__(self):
        return self.broker.name

class Agent(models.Model):
    id = models.CharField(primary_key=True, max_length=25, editable=False)
    # id = models.UUIDField(primary_key=True, default=uuid.uuid1, editable=False)
    name = models.CharField(max_length=100, null=False, unique=True) #必填
    description = models.CharField(max_length=255, null=True)
    status_list = (
        (0, '离线'), 
        (1, '健康')
    )
    status = models.IntegerField(choices=status_list, null=False, default=0)
    app_count = models.IntegerField(null=False, default=0)
    is_using = models.BooleanField(null=False, default=False)
    labels = ArrayField(models.CharField(max_length=20),null=True,blank=True,size=30,default=list)

    registrant = models.ForeignKey(
        User,
        editable=False,
        null=False,
        on_delete=models.CASCADE,
        related_name='agent_registrant')
    registered_at = models.DateTimeField(auto_now_add=True, editable=False)

    broker = models.ForeignKey(
        Broker,
        on_delete=models.CASCADE,
        related_name='broker',
        null=False)

    os = models.CharField(max_length=255, null=False)  #必填
    ip = models.CharField(max_length=100, null=False)  #必填
    docker_version = models.CharField(max_length=100, null=False) #必填
    cpu_cores = models.IntegerField(null=True)
    cpu_model_name = models.CharField(max_length=255, null=True)
    cpu_MHz = models.IntegerField(null=True)
    memory = models.IntegerField(null=True)
    gpu_cores = models.IntegerField(null=True)
    gpu_model_name = models.CharField(max_length=255, null=True)
    gpu_MHz = models.IntegerField(null=True)

    def __str__(self):
        return self.name

@receiver(post_delete, sender=Agent)
def auto_exit_agent(sender, instance, *args, **kwargs):
    if sender is Agent:
        channel_layer = get_channel_layer()
        _type = 'operate.agent_delete'
        async_to_sync(channel_layer.group_send)("controller", {"type": 'operate_agent', \
                'msg':{"operate":_type, "agent_id": str(instance.id)}})
    else:
        pass

class App(models.Model):
    id = models.CharField(primary_key=True, max_length=25, editable=False)
    # id = models.UUIDField(primary_key=True, default=uuid.uuid1, editable=False)
    # physical_topology = models.FileField(
    #     #file will be saved to MEDIA_ROOT/PhysicalTopolopy/2015/01/30
    #     blank=False, null=True, max_length=255, upload_to="PhysicalTopolopy/%Y/%m/%d")
    physical_topology = jsonfield.JSONField(default=dict,null=True)
    logical_topology = models.FileField(
        #file will be saved to MEDIA_ROOT/logicalTopolopy/2015/01/30
        blank=False, null=False, max_length=255, upload_to="logicalTopolopy/%Y/%m/%d")
    name = models.CharField(max_length=100,null=False)
    logical_topology_filename = models.CharField(max_length=100, null=False)
    status_list = (
        (0, '仅有逻辑拓扑'), 
        (1, '完成编排'), 
        (2, '应用运行中'), 
        (3, '应用已停止'), 
        (4, '编排中'), 
        (5, '控制器部署中'), 
        (6, '控制器启动中'), 
        (7, '停止中'), 
        (8, '卸载中'), 
        (9, '彻底清除中'),
        # (10, '控制器部署中'),
        (10, '应用组件部署中'),
        # (11, '控制器启动中'),
        (11, '应用组件启动中')
    )
    status = models.IntegerField(choices=status_list, null=False, default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True, editable=False, blank=True)
    modified_at = models.DateTimeField(auto_now_add=True, blank=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    uploader = models.ForeignKey(
        User,
        editable=False,
        null=False,
        on_delete=models.DO_NOTHING,
        related_name='uploader')
    # modifier = models.ForeignKey(
    #     User, 
    #     null=True, 
    #     on_delete=models.DO_NOTHING, 
    #     related_name='modifier')
    # containers = ArrayField(
    #     models.CharField(max_length=100),
    #     blank=True,
    #     default = list,
    #     size = 50
    # )
    def __str__(self):
        return self.name

@receiver(post_save, sender=App)
def operate(sender, instance, signal, *args, **kwargs):
    if sender is App:
        _status = instance.status
        map_to_operate = {
            4:'orchestrate',
            5:'up',
            6:'start',
            7:'stop',
            8:'down',
            9:'clean',
            10:'up',
            11: 'start'
        }
        channel_layer = get_channel_layer()
        print("=======_status==========")
        print(_status)
        if _status in [5,6,7,8,9]:
            _type = 'operate.app_'+map_to_operate[_status]
            if _status is 5:
                print("=======_status==========")
                print(_status)
                async_to_sync(channel_layer.group_send)("controller", {"type": 'operate_app', 'msg':{"operate":_type,  \
                                                    "app_id": str(instance.id), "parser_type":"controller","physical_topology":instance.physical_topology}})
            elif _status is 6:
                async_to_sync(channel_layer.group_send)("controller", {"type": 'operate_app', 'msg':{"operate":_type,  \
                                                    "app_id": str(instance.id), "parser_type":"controller","physical_topology":instance.physical_topology}})
            else:
                async_to_sync(channel_layer.group_send)("controller", {"type": 'operate_app', 'msg':{"operate":_type,  \
                                                    "app_id": str(instance.id),"physical_topology":instance.physical_topology}})
        elif _status is 10:
            _type = 'operate.app_'+map_to_operate[_status]
            async_to_sync(channel_layer.group_send)("controller", {"type": 'operate_app', 'msg':{"operate":_type,  \
                                                 "app_id": str(instance.id), "parser_type":"component","physical_topology":instance.physical_topology}})
        elif _status is 11:
            _type = 'operate.app_'+map_to_operate[_status]
            async_to_sync(channel_layer.group_send)("controller", {"type": 'operate_app', 'msg':{"operate":_type,  \
                                                 "app_id": str(instance.id), "parser_type":"component","physical_topology":instance.physical_topology}})
        
        elif _status is 4:
            _type = 'operate.app_'+map_to_operate[_status]
            async_to_sync(channel_layer.group_send)("orchestrator", {"type": 'orchestrate_app', "msg": {"app_id": str(instance.id)}})
    else:
        pass

@receiver(pre_save, sender=App)
def extract_logical_topology_metadata(sender, instance, *args, **kwargs):
    if sender is App:
        file = instance.logical_topology.file
        instance.logical_topology_filename = os.path.basename(file.name)
        #extract containers and devices
        # yaml_content = file.read().decode('utf-8')
        # res = yaml.load(yaml_content)
        # containers = list(res['containers'].keys())
        # devices = list(res['devices'])
        # instance.containers = containers
        # instance.devices = devices
    else:
        pass

#delete the file after the model is deleted
@receiver(post_delete, sender=App)
def auto_sender_cmd_to_controller_on_delete(sender, instance, *args, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `App` object is deleted.
    """
    # if instance.logical_topology:
    #     if os.path.isfile(instance.logical_topology.path):
    #         os.remove(instance.logical_topology.path)
    if sender is App:
        channel_layer = get_channel_layer()
        _type = 'operate.app_delete'
        async_to_sync(channel_layer.group_send)("controller", {"type": 'operate_app', 'msg':{"operate":_type,  \
                                                "app_id": str(instance.id),"physical_topology":instance.physical_topology}})
    else:
        pass
    #如果删除应用的时候应用处在已创建状态，那么删除应用后要更新device的app_count字段
    # if(instance.is_created):
    #     agent_list = Agent.objects.all()
    #     for agent_id in instance.devices:
    #         try:
    #             dev = agent_list.get(pk=agent_id)
    #             dev.app_count -= 1
    #             if(dev.app_count==0):
    #                 dev.is_using = False
    #             dev.save()
    #         except:
    #             pass

class Orchestration(models.Model):
    id = models.CharField(primary_key=True, max_length=25, editable=False)
    # id = models.UUIDField(primary_key=True, default=uuid.uuid1, editable=False)
    map_info = jsonfield.JSONField(default=dict,null=False)
    app = models.ForeignKey(
        App,
        on_delete=models.CASCADE,
        related_name='app',
        null=False)
    
    commited_at = models.DateTimeField(auto_now_add=True, editable=False)
    commiter = models.ForeignKey(
        User,
        editable=False,
        null=False,
        on_delete=models.CASCADE,
        related_name='commiter')
    def __str__(self):
        return str(self.id)

class AppContainerLog(models.Model):
    app = models.ForeignKey(
        App,
        editable=False,
        null=False,
        on_delete=models.CASCADE,
        related_name='appContainerLog_app')
    agent = models.ForeignKey(
        Agent,
        editable=True,
        null=False,
        on_delete=models.CASCADE,
        related_name='appContainerLog_agent')  
    container_name = models.CharField(max_length=100,null=False)
    timestamp = models.DateTimeField(auto_now_add=False, null=False)
    level_list = (
        (0, 'DEBUG'),
        (1, 'INFO'),
        (2, 'WARNING'),
        (3, 'ERROR'), 
        (4, 'CRITICAL')
    )
    level = models.IntegerField(choices=level_list, null=False, default=0)
    message = models.CharField(max_length=255,null=False)
    def __str__(self):
        return self.container_name


class ContainerStatus(models.Model):
    app = models.ForeignKey(
        App,
        editable=True,
        null=False,
        on_delete=models.CASCADE,
        related_name='containerStatus_app')
    agent = models.ForeignKey(
        Agent,
        editable=True,
        null=False,
        on_delete=models.CASCADE,
        related_name='containerStatus_agent')
    name = models.CharField(max_length=100,null=False)
    status_list = (
        (0, 'not-started'),
        (1, 'running'),
        (2, 'restarting'),
        (3, 'paused'), 
        (4, 'exited'),
        (5, 'created'),
        (6, 'ready')
    )
    status = models.IntegerField(choices=status_list, null=False, default=0)
    # container_type = controller/component
    container_type = models.CharField(max_length=100,null=False)
    def __str__(self):
        return self.name

@receiver(post_save, sender=ContainerStatus)
def container_operate(sender, instance, signal, *args, **kwargs):
    if sender is ContainerStatus:
        _status = instance.status
        if _status == 6:
            app = instance.app
            agent = instance.agent
            app_status = app.status
            app_controller_container = ContainerStatus.objects.filter(Q(app=app) & Q(container_type="controller"))
            print(type(app_controller_container))
            print(app_controller_container)
            app_controller_container_status_list = [cntr.status for cntr in app_controller_container]
            print(app_controller_container_status_list)
            print(app_status)
            if app_status == 5 and len(set(app_controller_container_status_list)) == 1 and 6 in set(app_controller_container_status_list):
                print("send componet up")
                app.status = 10
                app.save()
            if app_status == 6 and len(set(app_controller_container_status_list)) == 1 and 6 in set(app_controller_container_status_list):
                print("send componet start")
                app.status = 11
                app.save()


    



class ContainerData(models.Model):
    # id = models.UUIDField(primary_key=True, default=uuid.uuid1, editable=False)
    # info_id = models.AutoField(primary_key=True)
    app = models.ForeignKey(
        App,
        editable=True,
        null=False,
        on_delete=models.CASCADE,
        related_name='containerData_app')

    agent = models.ForeignKey(
        Agent,
        editable=True,
        null=False,
        on_delete=models.CASCADE,
        related_name='containerData_agent')

    timestamp = models.DateTimeField(auto_now_add=False, null=False)
    container_name = models.CharField(max_length=100,null=False)
    image_name = models.CharField(max_length=100,null=False)
    cpu_usage = models.CharField(max_length=100, null=True, default="0")
    mem_usage = models.CharField(max_length=100, null=True, default="0")
    mem_percent = models.CharField(max_length=100, null=True, default="0")
    net_in = models.CharField(max_length=100, null=True, default="0")
    net_out = models.CharField(max_length=100, null=True, default="0")
    create_at = models.CharField(max_length=100, null=True)
    status = models.CharField(max_length=100, null=True)
    platform = models.CharField(max_length=100, null=True)
    port_info = models.CharField(max_length=255, null=True)

    def __str__(self):
        return self.container_name

class AgentData(models.Model):
    # id = models.UUIDField(primary_key=True, default=uuid.uuid1, editable=False)
    # info_id = models.AutoField(primary_key=True)
    agent = models.ForeignKey(
        Agent,
        editable=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='AgentData_agent')

    timestamp = models.DateTimeField(auto_now_add=False, null=False)
    cpu_count = models.CharField(max_length=100,null=True, default="0")
    cpu_usage = models.CharField(max_length=100,null=True, default="0")
    mem_size = models.CharField(max_length=100,null=True, default="0")
    mem_usage = models.CharField(max_length=100,null=True, default="0")
    net_in = models.CharField(max_length=100, null=True, default="0")
    net_out = models.CharField(max_length=100, null=True, default="0")

    def __str__(self):
        return self.agent.name

# class AppDeployed(models.Model):
#     app = models.OneToOneField(App,on_delete=models.CASCADE,primary_key=True)
#     topology_json = models.TextField(null=False)
#     device_info = models.CharField(max_length=255,null=False)
#     app_uploader = models.ForeignKey(
#         User,
#         editable=False,
#         null=False,
#         on_delete=models.DO_NOTHING)
        
#     def __str__(self):
#         return self.app

# @receiver(pre_save, sender=AppDeployed)
# def add_device_info(sender, instance, signal, *args, **kwargs):
#     if sender is AppDeployed:
#         topology_json = instance.topology_json
#         topology_json_format = json.loads(topology_json)
#         print(topology_json_format)
#         device_info = {"device_info":[]}
#         print("devices-------------"+str(topology_json_format['devices']))
#         for device_id in topology_json_format['devices']:
#             device_is_cloud = Device.objects.get(pk=device_id).is_cloud
#             device_info["device_info"].append({"device":device_id,"is_cloud":device_is_cloud})
#         print(device_info)
#         instance.device_info = json.dumps(device_info)
#     else:
#         pass


