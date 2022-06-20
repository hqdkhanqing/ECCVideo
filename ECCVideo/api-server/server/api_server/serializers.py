from rest_framework import serializers 
from rest_framework.validators import UniqueValidator
import uuid
from .models import User, Agent, Orchestration, App, BrokerMonitor, \
    ContainerData, AgentData, Broker, Registry, ContainerStatus, AppContainerLog #,AppDeployed
from .fields import ArrayField
import shortuuid

# class LogicalTopologySerializer(serializers.ModelSerializer):
#     uploader = serializers.ReadOnlyField(source='uploader.username')
#     modifier = serializers.ReadOnlyField(source='modifier.username')
#     class Meta():
#         model = LogicalTopology
#         fields = '__all__'
#         read_only_fields = ('uploaded_at', 'modified_at','filename')
#         extra_kwargs = {
#                         'file':{'write_only':True},
#                         'description':{'required':False},
#                         'name':{'required':True},
#                         }

#         #When call .save(), the serializer will call create() if the app does not exist
#     def create(self,validated_data):
#         logical_topology = LogicalTopology(**validated_data)
#         logical_topology.save()
#         return logical_topology

# class MapSerializer(serializers.Serializer):
#     map_info=serializers.JSONField()
#     appname = serializers.CharField(max_length=100)
#     description = serializers.CharField(max_length=255,required=False)

class ContainerStatusSerializer(serializers.ModelSerializer):
    app_name = serializers.ReadOnlyField(source='app.appname')
    agent_name = serializers.ReadOnlyField(source='device.name')
    class Meta():
        model = ContainerStatus
        fields = '__all__'
        read_only_fields = ('status',)

class OrchestrationSerializer(serializers.ModelSerializer):
    commiter = serializers.ReadOnlyField(source='commiter.username')
    app_name = serializers.ReadOnlyField(source='app.name')
    map_info = serializers.JSONField()
    class Meta:
        model = Orchestration
        fields = '__all__'
        # fields = ("id", "map_info", "app", "commited_at", "commiter")
        read_only_fields = ('commited_at',)

    def create(self,validated_data):
        # print(validated_data)
        orchestration = Orchestration(**validated_data)
        orchestration.id = shortuuid.uuid()
        orchestration.save()
        return orchestration

class AgentSerializer(serializers.ModelSerializer):
    labels = ArrayField(default=[])
    # labels = serializers.CharField("")
    # labels = serializers.ListField(default = [])
    # labels = serializers.ListField(child=serializers.CharField(), allow_empty=True)
    registrant = serializers.ReadOnlyField(source='registrant.username')
    broker_name = serializers.ReadOnlyField(source='broker.name')
    is_cloud = serializers.ReadOnlyField(source='broker.is_cloud')
    class Meta:
        model = Agent
        fields = '__all__'
        read_only_fields = ('registered_at',
                            'is_using','status','app_count',)
        extra_kwargs = {
                        'labels': {'required': False},
                        }
        # read_only_fields = ('app_count', 'registered_at',
        #                     'is_using','topic',)

    def update(self, instance, validated_data):
        if hasattr(validated_data,'name'):
            del validated_data['name']
        return super(AgentSerializer,self).update(instance,validated_data)

    def create(self,validated_data):
        agent = Agent(**validated_data)
        agent.id = shortuuid.uuid()
        agent.save()
        return agent

class LabelsSerializer(serializers.Serializer):
    labels=ArrayField(default=[])

class BrokerSerializer(serializers.ModelSerializer):
    registrant = serializers.ReadOnlyField(source='registrant.username')
    class Meta:
        model = Broker
        fields = '__all__'
        read_only_fields = ('registered_at','status',)

    def create(self,validated_data):
        broker = Broker(**validated_data)
        broker.id = shortuuid.uuid()
        broker.save()
        return broker

class RegistrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Registry
        fields = '__all__'
        read_only_fields = ('status',)

    def create(self,validated_data):
        registry = Registry(**validated_data)
        registry.id = shortuuid.uuid()
        registry.save()
        return registry

class BrokerMonitorSerializer(serializers.ModelSerializer):
    broker_name = serializers.ReadOnlyField(source='broker.name')
    class Meta():
        model = BrokerMonitor
        fields = '__all__'
        read_only_fields = ('status',)


class UserSerializer(serializers.ModelSerializer):
    username=serializers.CharField(validators=[UniqueValidator(queryset=User.objects.all())])
    class Meta(object):
        model = User
        exclude=('jwt_secret','groups','user_permissions')
        read_only_fields=('date_joined','last_login','is_staff','is_superuser','is_active',)
        extra_kwargs = {
            'password': {'write_only': True},
        }
    
    def validate_password(self, attrs):
        password_min_length = 6
        password_length = len(attrs)
        if password_length < password_min_length:
            raise serializers.ValidationError(('Ensure this value has at least %d characters (it has %d).') % (password_min_length, password_length))
        return attrs

    #When call .save(), the serializer will call create() if the user does not exist
    def create(self,validated_data):
        user = User(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

    #When call .save(), the serializer will call update() if the user exists
    def update(self, instance, validated_data):
        instance.username=validated_data.get('username',instance.username)
        instance.first_name=validated_data.get('first_name',instance.first_name)
        instance.last_name=validated_data.get('last_name',instance.last_name)
        instance.email=validated_data.get('email',instance.email)
        if validated_data.get('password',None):
            instance.set_password(validated_data['password'])
            instance.jwt_secret = uuid.uuid4()
        instance.save()
        return instance

class SimplifiedUserSerializer(serializers.ModelSerializer,serializers.ReadOnlyField):
    class Meta(object):
        model = User
        fields=('id','username')
    
class PasswordSerializer(serializers.Serializer):
    password=serializers.CharField(min_length=6)
    new_password = serializers.CharField(min_length=6)

class URISerializer(serializers.Serializer):
    uri=serializers.CharField()

class OperationSerializer(serializers.Serializer):
    operate = serializers.ChoiceField(choices=['orchestrate', 'up', 'start', 'stop', 'down', 'clean', 'return0','return1','return2','return3','return4','return5'])

class AppSerializer(serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source='uploader.username')
    class Meta():
        model = App
        fields = '__all__'
        read_only_fields = ('uploaded_at', 'modified_at','logical_topology_filename',
                            'physical_topology_filename', 'status', 'physical_topology')
        extra_kwargs = {
                        'logical_topology':{'write_only':True},
                        'description':{'required':False},
                        # 'containers': {'required':False},
                        # 'devices': {'required':False},
                        'appname':{'required':True},
                        }

        #When call .save(), the serializer will call create() if the app does not exist
    def create(self,validated_data):
        app = App(**validated_data)
        app.id = shortuuid.uuid()
        app.save()
        return app

class AppContainerLogSerializer(serializers.ModelSerializer):
    app_name = serializers.ReadOnlyField(source='app.name')
    broker_name = serializers.ReadOnlyField(source='agent.broker.name')
    agent_name = serializers.ReadOnlyField(source='agent.name')
    class Meta():
        model = AppContainerLog
        fields = '__all__'

class ContainerDataSerializer(serializers.ModelSerializer):

    # app_id = serializers.ReadOnlyField(source='app.id')
    app_name = serializers.ReadOnlyField(source='app.name')
    # device_id = serializers.ReadOnlyField(source='device.id')
    agent_name = serializers.ReadOnlyField(source='agent.name')
    class Meta():
        model = ContainerData
        fields = '__all__'
        # exclude = ['app', 'device']
    
class AgentDataSerializer(serializers.ModelSerializer):

    # device_id = serializers.ReadOnlyField(source='device.id')
    agent_name = serializers.ReadOnlyField(source='agent.name')
    class Meta():
        model = AgentData
        fields = '__all__'
        # exclude = ['device'] 

# class AppDeployedSerializer(serializers.ModelSerializer):
#     app_id = serializers.ReadOnlyField(source='app.id')
#     app_name = serializers.ReadOnlyField(source='app.appname')
#     app_uploader = serializers.ReadOnlyField(source='app_uploader.username')
#     class Meta():
#         model = AppDeployed
#         # fields = '__all__'
#         exclude = ['app',]
#         read_only_fields = ('device_info', )
