from rest_framework.parsers import MultiPartParser, FormParser,JSONParser
from rest_framework.response import Response
from rest_framework.decorators import authentication_classes,permission_classes,action
from rest_framework import status, generics, viewsets, permissions, mixins
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404,render
from django.http import HttpResponse
from django.contrib.auth import user_logged_in
from rest_framework_jwt.utils import jwt_payload_handler, jwt
from django_filters import rest_framework as filters
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView
from rest_framework import status
from rest_framework import serializers
from rest_framework.permissions import AllowAny,IsAuthenticated,IsAdminUser
from django.db.models import F, Q
from .serializers import URISerializer,AppSerializer, LabelsSerializer, AgentSerializer, UserSerializer,PasswordSerializer,OperationSerializer,BrokerMonitorSerializer, \
ContainerDataSerializer,ContainerStatusSerializer,AppContainerLogSerializer,AgentDataSerializer,RegistrySerializer,BrokerSerializer,OrchestrationSerializer #,AppDeployedSerializer
from .models import App, Agent, Orchestration, User, AppContainerLog, ContainerData, ContainerStatus, AgentData, Broker,Registry,BrokerMonitor # AppDeployed ,DeviceLocation
from drf_signed_auth.authentication import SignedURLAuthentication

from rest_framework import HTTP_HEADER_ENCODING
import json
from django.urls import reverse
from django.utils import timezone
from .utils import *
from .permissions import IsSuperUser,IsSuperUserOrOwner,IsStaffOrOwner,IsStaffOrUploader,IsStaffOrRegistrant, IsStaffOrCommiter
import uuid
from django.db import models
from rest_framework.settings import api_settings
import os
import shutil
import time
from django.core.files import File as djangoFile

# import the custom pagination styles
from .pagination import ResultSetPagination
from rest_framework.pagination import PageNumberPagination
from django.utils.safestring import mark_safe

#import third-party packages
import yaml

class RevokeJSONWebToken(APIView):
    """
    Use this endpoint to log out all sessions for a given user.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        user.jwt_secret = uuid.uuid4()
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


#‘/api/users/’
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer  #serializer中定义的field会被用于自带方法，比如create()
    parser_classes = [MultiPartParser, FormParser,JSONParser]
    filter_backends = (DjangoFilterBackend,)
    filter_fields=('is_active','is_superuser','is_staff')

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create']:
            permission_classes = [AllowAny]
        elif self.action in ['get_current_user']:
            permission_classes = [IsAuthenticated]
        elif self.action in ['list','retrieve']:
            permission_classes = [IsAuthenticated,IsAdminUser]
        elif self.action in ['update','partial_update','change_password']:
            permission_classes = [IsAuthenticated,IsSuperUserOrOwner]
        else:
            permission_classes = [IsAuthenticated,IsSuperUser]
        return [permission() for permission in permission_classes]

    def perform_destroy(self,instance):
        instance.is_active=False
        instance.save()

    #'api/users/get_current_user'  
    @action(detail=False,methods=['get'])     
    def get_current_user(self, request):
        current_user=get_object_or_404(self.get_queryset(),pk=request.user.id)
        serializer = self.serializer_class(current_user)
        return Response(serializer.data)

    # 'api/users/{pk}/activate'
    @action(detail=True,methods=['post'],serializer_class=serializers.Serializer)     
    def activate(self, request, pk=None):
        user=get_object_or_404(self.get_queryset(),pk=pk)
        user.is_active=True
        user.save()
        return Response(status=status.HTTP_200_OK,data={'msg':'修改成功'})

    # 'api/users/{pk}/deactivate'
    @action(detail=True,methods=['post'],serializer_class=serializers.Serializer) 
    def deactivate(self, request, pk=None):
        user=get_object_or_404(self.get_queryset(),pk=pk)
        user.is_active=False
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT,data={'msg':'修改成功'})

    # 'api/users/{pk}/set_superuser'
    @action(detail=True,methods=['post'],serializer_class=serializers.Serializer)   
    def set_superuser(self, request, pk=None):
        user=get_object_or_404(self.get_queryset(),pk=pk)
        user.is_superuser=True
        user.is_staff=True
        user.save()
        return Response(status=status.HTTP_200_OK,data={'msg':'修改成功'})
    
    # 'api/users/{pk}/unset_superuser'
    @action(detail=True,methods=['post'],serializer_class=serializers.Serializer)  
    def unset_superuser(self, request, pk=None):
        user=get_object_or_404(self.get_queryset(),pk=pk)
        user.is_superuser=False
        user.save()
        return Response(status=status.HTTP_200_OK,data={'msg':'修改成功'})

    #'api/users/{pk}/set_staff'
    @action(detail=True,methods=['post'],serializer_class=serializers.Serializer)  
    def set_staff(self, request, pk=None):
        user=get_object_or_404(self.get_queryset(),pk=pk)
        user.is_staff=True
        user.save()
        return Response(status=status.HTTP_200_OK,data={'msg':'修改成功'})
    
    #'api/users/{pk}/unset_staff'
    @action(detail=True,methods=['post'],serializer_class=serializers.Serializer) 
    def unset_staff(self, request, pk=None):
        user=get_object_or_404(self.get_queryset(),pk=pk)
        user.is_staff=False
        user.is_superuser=False
        user.save()
        return Response(status=status.HTTP_200_OK,data={'msg':'修改成功'})

    #'api/users/{pk}/change_password'
    @action(detail=True,methods=['post'],serializer_class=PasswordSerializer)  
    def change_password(self, request, pk=None):
        user = get_object_or_404(self.get_queryset(),pk=pk)
        self.check_object_permissions(request,user)
        serializer = PasswordSerializer(data=request.data,partial=True)
        if serializer.is_valid():
            #use built-in method check_password to check original password 
            if(user.check_password(serializer.validated_data['password'])):
                user.set_password(serializer.validated_data['new_password'])
                user.jwt_secret = uuid.uuid4()
                user.save()
                return Response(status=status.HTTP_200_OK,data={'msg':'修改成功'})
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST,data={'msg':'原始密码错误'})
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

class RegistryViewSet(viewsets.ModelViewSet):
    queryset = Registry.objects.all().order_by('name')
    serializer_class = RegistrySerializer
    parser_classes = [MultiPartParser, FormParser,JSONParser]
    filter_backends = (DjangoFilterBackend,)
    filter_fields=('status',)

    def get_permissions(self):
        permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    # def get_queryset(self):
    #     user = self.request.user
    #     if user.is_superuser or user.is_staff:
    #         return  Registry.objects.all().order_by('name')
    #     else:
    #         return  Registry.objects.filter(Q(owner=user.id) | Q(is_public=True)).order_by('name')

class BrokerMonitorViewSet(viewsets.ModelViewSet):
    queryset = BrokerMonitor.objects.all()
    serializer_class = BrokerMonitorSerializer
    parser_classes = [MultiPartParser, FormParser,JSONParser]
    filter_backends = (DjangoFilterBackend,)
    filter_fields=('status',)

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        broker_id_list = []
        if user.is_superuser or user.is_staff:
            return BrokerMonitor.objects.all()
        else:
            brokers = Broker.objects.filter(registrant=user.id)
        for broker in brokers:
            broker_id_list.append(broker.id)
        else:
            return BrokerMonitor.objects.filter(broker__in=broker_id_list)


class BrokerViewSet(viewsets.ModelViewSet):
    queryset = Broker.objects.all().order_by('name')
    serializer_class = BrokerSerializer
    parser_classes = [MultiPartParser, FormParser,JSONParser]
    filter_backends = (DjangoFilterBackend, OrderingFilter,)
    filter_fields=('is_cloud','registrant',)

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create','list']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated,IsStaffOrRegistrant]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return  Broker.objects.all().order_by('name')
        else:
            return  Broker.objects.filter(registrant=user.id).order_by('name')

    # def perform_create(self, serializer):
    #     user = self.request.user
    #     serializer.save(registrant=self.request.user)

    def create(self, request):
        serializer = self.serializer_class(data = request.data)
        user = request.user
        # print(request.data)
        if "is_cloud" not in request.data:
            if request.data['mountpoint'] == "":
                return Response({'msg': "创建失败,边缘云broker必须填写mountpoint-格式应为(.*/)"}, status=status.HTTP_400_BAD_REQUEST)
            # elif request.data['mountpoint'] == 'null': 
            #     return Response({'msg': "创建失败,边缘云broker必须填写mountpoint-格式应为(.*/)"}, status=status.HTTP_400_BAD_REQUEST)
            elif request.data['mountpoint'][-1] != '/' or '/' in request.data['mountpoint'][0:-1]:
                return Response({'msg': "创建失败,mountpoint格式应为(.*/)"}, status=status.HTTP_400_BAD_REQUEST)
        if(serializer.is_valid()):
            serializer.save(registrant=self.request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AgentFilter(filters.FilterSet):
    registered_at = filters.DateTimeFromToRangeFilter(field_name='registered_at')
    class Meta:
        model = Agent
        fields = ['id', 'is_using']

class AgentViewSet(viewsets.ModelViewSet):
    queryset = Agent.objects.all().order_by('id')
    serializer_class = AgentSerializer
    parser_classes = [MultiPartParser, FormParser,JSONParser]
    filter_backends = (SearchFilter, DjangoFilterBackend,)
    search_fields = ('name', 'description',)
    filter_class = AgentFilter
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create','list']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated,IsStaffOrRegistrant]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return  Agent.objects.all().order_by('id')
        else:
            return  Agent.objects.filter(Q(registrant=user.id)).order_by('id')
            # return  Agent.objects.filter(Q(registrant=user.id) | Q(is_public=True)).order_by('id')

    def create(self, request):
        data = request.POST
        if not request.data['labels']:
            _mutable = data._mutable
            data._mutable = True
            data['labels'] = '[""]'
            data._mutable = _mutable
        elif request.data['labels'] == "null":
            _mutable = data._mutable
            data._mutable = True
            data['labels'] = '[""]'
            data._mutable = _mutable
        serializer = self.serializer_class(data = data)
        user = request.user
        broker_id = request.data['broker']
        broker = Broker.objects.get(pk=broker_id)
        if(serializer.is_valid()):
            if user.id is broker.registrant.id:
                serializer.save(registrant=self.request.user)
                res_msg = serializer.data
                res_msg['command'] = 'docker run -d -e BROKER_IP=%s -e BROEKR_PORT=%s agent'%(str(broker.ip), str(broker.port))
                return Response(res_msg, status=status.HTTP_201_CREATED)
            else:
                return Response({'msg': "无法向该Broker注册设备"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # return Response({'msg': "创建失败"}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True,methods=['get'],serializer_class=LabelsSerializer)  
    def get_labels(self, request, pk=None):
        agent=get_object_or_404(self.get_queryset(),pk=pk)
        self.check_object_permissions(request,agent)
        serializer=LabelsSerializer(data={"labels":agent.labels})
        serializer.is_valid()
        return Response(serializer.data,status=status.HTTP_200_OK)

    @action(detail=True,methods=['post'],serializer_class=LabelsSerializer) 
    def set_labels(self, request, pk=None):
        agent=get_object_or_404(self.get_queryset(),pk=pk)
        self.check_object_permissions(request,agent)
        serializer = LabelsSerializer(data=request.data,partial=True)
        if serializer.is_valid():
            agent.labels=serializer.data['labels']
            agent.save()
            return Response(status=status.HTTP_200_OK,data={'msg':'修改成功'})
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False,methods=['post'],serializer_class=AgentSerializer) 
    def bulk_register(self, request, pk=None):
        agent_bulk_file = request.FILES.get('agent_bulk_file')
        success_msg = []
        serializer_list = []
        if agent_bulk_file:
            contents = yaml.load(agent_bulk_file.read())
            for each_agent in contents['agents']:
                serializer = self.serializer_class(data = each_agent)
                if serializer.is_valid():
                    serializer_list.append(serializer)
                else:
                    return Response(data={'存在格式错误的agent':each_agent['name'],'格式错误描述':serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
            for serializer_item in serializer_list:
                serializer_item.save(registrant=self.request.user)
                success_msg.append(serializer_item.data)
            return Response(status=status.HTTP_200_OK,data={'agents':success_msg})
        return Response(status=status.HTTP_400_BAD_REQUEST,data={'msg':'无批量设备注册文件上传'})

    # 删除agent
    def destroy(self, request, pk=None):

        print("delete agent")
        agent = self.get_queryset().filter(pk = pk)[0]
        # agent_id = agent.id
        containerStatus_list = ContainerStatus.objects.filter(agent=agent)
        if len(containerStatus_list) == 0:
            agent.delete()
            return Response(status=status.HTTP_200_OK,data={'msg':"delete success"})
            
        else:
            msg = f"{agent.name} 存在应用依赖，无法删除"
            return Response(status=status.HTTP_400_BAD_REQUEST,data={'msg':msg})





class OrchestrationViewSet(viewsets.ModelViewSet):
    queryset = Orchestration.objects.all().order_by('commited_at')
    serializer_class = OrchestrationSerializer
    parser_classes = [MultiPartParser, FormParser,JSONParser]
    filter_backends = (DjangoFilterBackend, OrderingFilter,)
    # filter_fields=('commiter')

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create','list']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated,IsStaffOrCommiter]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return  Orchestration.objects.all().order_by('commited_at')
        else:
            return  Orchestration.objects.filter(commiter=user.id).order_by('commited_at')

    def create(self, request):
        serializer = self.serializer_class(data = request.data)
        user = request.user
        app_id = request.data['app']
        app = get_object_or_404(App, pk=app_id)
        if(serializer.is_valid()):
            try:
                map_info = json.loads(request.data['map_info'])
                policy = map_info['policy']
                agent_list = []
                for item in map_info['maps']:
                    if 'agent' in item:
                        agent_id = item['agent']
                        agent = Agent.objects.get(pk=agent_id)
                        agent_list.append(agent)
            except:
                return Response({'msg': "编排信息格式不正确或所选agent_id不存在"}, status=status.HTTP_400_BAD_REQUEST)
            # if app.uploader.id is self.request.user.id and app.status != 4:
            if app.uploader.id is self.request.user.id:
                app.status = 4
                serializer.save(commiter=self.request.user,app = app)
                app.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            elif app.uploader.id is not self.request.user.id:
                return Response({'msg': "无该应用编排权限"}, status=status.HTTP_400_BAD_REQUEST)
            # else:
            #     return Response({'msg': "该应用正处于编排中"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'msg': "提交失败"}, status=status.HTTP_400_BAD_REQUEST)

class AppFilter(filters.FilterSet):
    uploaded_at = filters.DateTimeFromToRangeFilter(field_name='uploaded_at')
    modified_at = filters.DateTimeFromToRangeFilter(field_name='modified_at')
    # size = filters.NumericRangeFilter(field_name='size')
    class Meta:
        model = App
        fields = ['id', 'status']

class AppViewSet(viewsets.ModelViewSet):
    queryset = App.objects.all().order_by('-modified_at')
    serializer_class = AppSerializer
    parser_classes = [MultiPartParser, FormParser,JSONParser]
    filter_backends = (SearchFilter, DjangoFilterBackend, OrderingFilter,)
    filter_class = AppFilter
    fields = ('uploaded_at', 'modified_at', 'name', 'description','status')
    search_fields = ('name','description',)
    ordering_fields = ('modified_at', 'uploaded_at',)

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list','create']:
            permission_classes = [IsAuthenticated]
        elif self.action in ['get_uri']:
            permission_classes=[IsAuthenticated,IsAdminUser]
        else:
            permission_classes = [IsAuthenticated,IsStaffOrUploader]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return  App.objects.all().order_by('-modified_at')
        else:
            return  App.objects.filter(uploader=user.id).order_by('-modified_at')
            # logical_topology_list = LogicalTopology.objects.filter(uploader=user.id)
            # id_list = []
            # for logical_topology_item in logical_topology_list:
            #     id_list.append(logical_topology_item.id)
            # return  App.objects.filter(logical_topology__in=id_list).order_by('-modified_at')

    def perform_create(self, serializer):
        serializer.save(uploaded_at=timezone.now(),uploader=self.request.user)

    def perform_update(self, serializer):
        serializer.save(modified_at=timezone.now())

    @action(detail=True,methods=['get'],serializer_class=serializers.Serializer) 
    def get_uri(self, request, pk=None):
        app = get_object_or_404(self.get_queryset(), pk=pk)
        return Response({'uri':app.logical_topology.path},status=status.HTTP_200_OK)

    @action(detail=True,methods=['get'],serializer_class=serializers.Serializer) 
    def get_download_url(self, request, pk=None):
        app = get_object_or_404(self.get_queryset(), pk=pk)
        app.save()
        #generated an url like /api/apps/37fc22e4-56ba-11e9-b882-c8e0eb18e6a7/download/testapp_anzdh28.yaml
        url=reverse('apps-download',kwargs={'pk':pk,'filename':app.logical_topology_filename})
        return Response({'url':get_signed_url(request,url)},status=status.HTTP_200_OK)


    ###应用操作
    @action(detail=True,methods=['post'],serializer_class=OperationSerializer) 
    def operation(self, request, pk=None):
        app=self.get_object()
        serializer = OperationSerializer(data=request.data,partial=True)
        if serializer.is_valid():
            _choice = serializer.data['operate']
            print("====_choice=======")
            print(_choice)
            map_to_status = {
                'orchestrate':{'from':[0,1,4],'to':4},
                'up':{'from':[1,2,5,6],'to':5},
                'start':{'from':[3],'to':6},
                'stop':{'from':[2],'to':7},
                'down':{'from':[2,3],'to':8},
                'clean':{'from':[2,3],'to':9},
                'return0':{'from':[0,1,2,3,4,5,6,7,8,9,10],'to':0},
                'return1':{'from':[0,1,2,3,4,5,6,7,8,9,10],'to':1},
                'return2':{'from':[0,1,2,3,4,5,6,7,8,9,10],'to':2},
                'return3':{'from':[0,1,2,3,4,5,6,7,8,9,10],'to':3},
                'return4':{'from':[0,1,2,3,4,5,6,7,8,9,10],'to':4},
                'return5':{'from':[0,1,2,3,4,5,6,7,8,9,10],'to':5}
            }
            _status = app.status
            if _status in map_to_status[_choice]['from']:
                app.status = map_to_status[_choice]['to']
                app.save()
                return Response(status=status.HTTP_200_OK,data={'msg':'修改成功'})
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST,data={'msg':'应用当前状态不支持该操作'})
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    # def destroy(self, request, pk=None):
    #     print("=========delete click=======")
    #     # 发送请求给agent删除相关数据
    #     app = self.get_queryset().filter(pk = pk)[0]
    #     # pub
    #     topic = 'req/app_manage/'+str(app.id)+'/delete'
    #     payload = str(app.id)
    #     result = pub_to_driver_program(topic,payload)
    #     print("==============result=",result)
    #     msg = ""
    #     app.delete()
    #     msg = "successed"
    #     return Response({'msg': msg},status=status.HTTP_200_OK)

class ContainerStatusViewSet(viewsets.ModelViewSet):
    queryset = ContainerStatus.objects.all()
    serializer_class = ContainerStatusSerializer 
    parser_classes = [MultiPartParser, FormParser,JSONParser]
    filter_backends = (DjangoFilterBackend,)
    filter_fields=('app',)
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        # if self.action not in ['create']:
        permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        app_id_list = []
        if user.is_superuser or user.is_staff:
            Apps = App.objects.all()
        else:
            Apps = App.objects.filter(uploader=user.id)
        for app in Apps:
            app_id_list.append(app.id)
        else:
            return ContainerStatus.objects.filter(app__in=app_id_list)


#‘/api/containersData/’
class ContainerDataViewSet(viewsets.ModelViewSet):
    queryset = ContainerData.objects.all().order_by('-timestamp')
    serializer_class = ContainerDataSerializer 
    parser_classes = [MultiPartParser, FormParser,JSONParser]
    filter_backends = (DjangoFilterBackend,)
    filter_fields=('app','agent','container_name')

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        app_id_list = []
        if user.is_superuser or user.is_staff:
            Apps = App.objects.all()
        else:
            Apps = App.objects.filter(uploader=user.id)
        for app in Apps:
            app_id_list.append(app.id)
        return ContainerData.objects.filter(app__in=app_id_list)


#‘/api/devicesData/’
class AgentDataViewSet(viewsets.ModelViewSet):
    queryset = AgentData.objects.all().order_by('-timestamp')
    serializer_class = AgentDataSerializer
    parser_classes = [MultiPartParser, FormParser,JSONParser]
    filter_backends = (DjangoFilterBackend,)
    filter_fields=('agent',)

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        device_id_list = []
        if user.is_superuser or user.is_staff:
            Devices = Agent.objects.all()
        else:
            Devices = Agent.objects.filter(registrant=user.id)
        for device in Devices:
            device_id_list.append(device.id)
        return AgentData.objects.filter(agent__in=device_id_list).order_by('-timestamp')


#‘/api/appContainerLog/’
class AppContainerLogViewSet(viewsets.ModelViewSet):
    queryset = AppContainerLog.objects.all().order_by('-timestamp')
    serializer_class = AppContainerLogSerializer
    parser_classes = [MultiPartParser, FormParser,JSONParser]
    filter_backends = (DjangoFilterBackend,)
    filter_fields=('app','agent','container_name')

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        device_id_list = []
        if user.is_superuser or user.is_staff:
            Devices = Agent.objects.all()
        else:
            Devices = Agent.objects.filter(registrant=user.id)
        for device in Devices:
            device_id_list.append(device.id)
        return AppContainerLog.objects.filter(agent__in=device_id_list).order_by('-timestamp')


# #‘/api/appDeployed/’
# class AppDeployedViewSet(viewsets.ModelViewSet):
#     queryset = AppDeployed.objects.all()
#     serializer_class = AppDeployedSerializer
#     parser_classes = [MultiPartParser, FormParser,JSONParser]
#     filter_backends = (DjangoFilterBackend,)
#     filter_fields=('app',)
#     def get_permissions(self):
#         """
#         Instantiates and returns the list of permissions that this view requires.
#         """
#         permission_classes = [IsAuthenticated]
#         return [permission() for permission in permission_classes]

#     def get_queryset(self):
#         user = self.request.user
#         if user.is_superuser or user.is_staff:
#             return  AppDeployed.objects.all()
#         else:
#             return  AppDeployed.objects.filter(app_uploader=user.id)

#     # def perform_create(self, serializer):
#     #     app_id = self.request.data['app']
#     #     app = App.objects.get(pk=app_id)
#     #     app_uploader = User.objects.get(pk=app.uploader.id)
#     #     serializer.save(app=app,app_uploader=app_uploader)

#     def create(self, request):

#         app_id = request.data['app']

#         serializer = self.serializer_class(data = request.data)
#         if(serializer.is_valid()):
#             # try:
#             app = App.objects.get(pk=app_id)
#             app_uploader = User.objects.get(pk=app.uploader.id)
#             serializer.save(app=app,app_uploader=app_uploader)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#             # except:
#                 # return Response({'msg': "添加失败"}, status=status.HTTP_400_BAD_REQUEST)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#文件直接下载api
# class LogicalTopologyDownloadAPIView(APIView):
#     authentication_classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES+[
#         SignedURLAuthentication
#     ]

#     def get_queryset(self):
#         user = self.request.user
#         if user.is_superuser or user.is_staff:
#             return  LogicalTopology.objects.all()
#         else:
#             return  LogicalTopology.objects.filter(uploader=user.id)

#     def get(self, request, pk=None,filename=None):
#         logical_topology = get_object_or_404(self.get_queryset(), pk=pk)
#         self.check_object_permissions(request,logical_topology)
#         return sendfile(request,logical_topology.file.url,logical_topology.file.path)

# logical_topology_download_view = LogicalTopologyDownloadAPIView.as_view()


#文件直接下载api
class AppDownloadAPIView(APIView):
    authentication_classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES+[
        SignedURLAuthentication
    ]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return  App.objects.all()
        else:
            return  App.objects.filter(uploader=user.id)

    def get(self, request, pk=None,filename=None):
        app = get_object_or_404(self.get_queryset(), pk=pk)
        self.check_object_permissions(request,app)
        return sendfile(request,app.logical_topology.url,app.logical_topology.path)
    
app_download_view = AppDownloadAPIView.as_view()


#下载agent 容器依赖的.env文件
class AgentENVDownloadAPIView(APIView):
    authentication_classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES+[
        SignedURLAuthentication
    ]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return  Agent.objects.all()
        else:
            return  Agent.objects.filter(uploader=user.id)
    
    def get(self, request, pk=None,filename=None):
        agent = get_object_or_404(self.get_queryset(), pk=pk)
        broker = agent.broker
        self.check_object_permissions(request,agent)
        self.check_object_permissions(request,broker)

        ECCI_BROKER_IP = os.getenv("ECCI_BROKER_IP",default="localhost")
        ECCI_BROKER_PORT = os.getenv("ECCI_BROKER_PORT",default="1883")

        content = f"ECCI_BROKER_IP={ECCI_BROKER_IP}\nECCI_BROKER_PORT={ECCI_BROKER_PORT}\nECCI_AGENT_ID={agent.id}\nECCI_MQTT_CLIENT_ID={agent.id}\nECCI_USERNAME=\nECCI_PASSWORD=\nECCI_LOCAL_BROKER_IP={broker.ip}\nECCI_LOCAL_BROKER_PORT={broker.port}\nECCI_LOCAL_BROKER_ID={broker.id}\nECCI_LOCAL_BROKER_USERNAME=\nECCI_LOCAL_BROKER_PASSWORD=\nECCI_REGISTRY_URL=\nECCI_REGISTRY_USERNAME=\nECCI_REGISTRY_PASSWORD="
        # return sendfile(request,Agent,Broker)
        # print(content)
        filename = ".env"
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="{0}"'.format(filename)
        return response
        # return HttpResponse(content, content_type='text/plain')
    
agent_ENV_download_view = AgentENVDownloadAPIView.as_view()

#下载broker 容器依赖的桥接env文件
class BrokerENVDownloadAPIView(APIView):
    authentication_classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES+[
        SignedURLAuthentication
    ]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return  Broker.objects.all()
        else:
            return  Broker.objects.filter(id=user.id)
    def get_cloud_broker_queryset(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return  Broker.objects.filter(Q(id=user.id) | Q(is_cloud=True))
        else:
            return  Broker.objects.filter(Q(id=user.id) | Q(is_cloud=True))
    
    def get(self, request, pk=None,filename=None):
        self_broker = get_object_or_404(self.get_queryset(), pk=pk)
        self.check_object_permissions(request,self_broker)

        if self_broker.is_cloud:
            content = f"ECCI_CLOUD_BROKER_PORT={self_broker.port}"
        else:
            edge_broker = self_broker
            # cloud_broker = Broker.objects.filter(Q(registrant=request.user.id) | Q(is_cloud=True))[0]
            cloud_broker = get_object_or_404(self.get_cloud_broker_queryset())
            self.check_object_permissions(request,cloud_broker)
            
            # ECCI_BROKER_IP = os.getenv("ECCI_BROKER_IP",default="localhost")
            # ECCI_BROKER_PORT = os.getenv("ECCI_BROKER_PORT",default="1883")

            # content = f"ECCI_BROKER_IP=\nECCI_BROKER_PORT=1883\nECCI_AGENT_ID={agent.id}\nECCI_MQTT_CLIENT_ID={agent.id}\nECCI_USERNAME=\nECCI_PASSWORD=\nECCI_LOCAL_BROKER_IP={broker.ip}\nECCI_LOCAL_BROKER_PORT={broker.port}\nECCI_LOCAL_BROKER_ID={broker.id}\nECCI_LOCAL_BROKER_USERNAME=\nECCI_LOCAL_BROKER_PASSWORD=\nECCI_REGISTRY_URL=\nECCI_REGISTRY_USERNAME=\nECCI_REGISTRY_PASSWORD="
            content = f"EMQX_BRIDGE__MQTT__EDGEAI__ADDRESS={cloud_broker.ip}:{cloud_broker.port}\nEMQX_BRIDGE__MQTT__EDGEAI__MOUNTPOINT={edge_broker.mountpoint}\nEMQX_BRIDGE__MQTT__EDGEAI__FORWARDS=ECCI/{cloud_broker.id}/#\nEMQX_BRIDGE__MQTT__EDGEAI__SUBSCRIPTION__1__TOPIC=ECCI/{edge_broker.id}/#\nEMQX_BRIDGE_NAME={edge_broker.name}\nECCI_EDGE_BROKER_PORT={edge_broker.port}"
        # return sendfile(request,Agent,Broker)
        # print(content)
        filename = ".env"
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="{0}"'.format(filename)
        return response
        # return HttpResponse(content, content_type='text/plain')
    
broker_ENV_download_view = BrokerENVDownloadAPIView.as_view()



#下载 usermonitor 容器依赖的env文件
class UserMonitorENVDownloadAPIView(APIView):
    authentication_classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES+[
        SignedURLAuthentication
    ]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return  Broker.objects.all()
        else:
            return  Broker.objects.filter(id=user.id)
    
    def get(self, request, pk=None,filename=None):
        local_broker = get_object_or_404(self.get_queryset(), pk=pk)
        self.check_object_permissions(request,local_broker)

        
        ECCI_BROKER_IP = os.getenv("ECCI_BROKER_IP",default="localhost")
        ECCI_BROKER_PORT = os.getenv("ECCI_BROKER_PORT",default="1883")

        content = f"ECCI_MONITOR_MODE=user\nECCI_MONITOR_SOURCE_IP={local_broker.ip}\nECCI_MONITOR_SOURCE_PORT={local_broker.port}\nECCI_MONTTOR_SOURCE_USERNAME=\nECCI_MONITOR_SOURCE_PASSWORD=\nECCI_MONITOR_FORWARD_BROKER_ID={local_broker.id}\nECCI_MONITOR_FORWARD_IP={ECCI_BROKER_IP}\nECCI_MONITOR_FORWARD_PORT={ECCI_BROKER_PORT}\nECCI_MONITOR_FORWARD_USERNAME=\nECCI_MONITOR_FORWARD_PASSWORD=\nECCI_MONITOR_SOURCE_SUB_TOPIC="
        filename = ".env"
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="{0}"'.format(filename)
        return response
        # return HttpResponse(content, content_type='text/plain')
    
usermonitor_ENV_download_view = UserMonitorENVDownloadAPIView.as_view()


#下载 file_manager 容器依赖的env文件
class FileManagerENVDownloadAPIView(APIView):
    authentication_classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES+[
        SignedURLAuthentication
    ]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return  Broker.objects.all()
        else:
            return  Broker.objects.filter(id=user.id)

    def get(self, request, pk=None,filename=None):
        local_broker = get_object_or_404(self.get_queryset(), pk=pk)
        self.check_object_permissions(request,local_broker)
        if local_broker.is_cloud:
            ECCI_MINIO_MODE = 'cloud'
        else:
            ECCI_MINIO_MODE = 'edge'

        content = f"ECCI_MINIO_MODE={ECCI_MINIO_MODE}\nECCI_LOCAL_BROKER_IP={local_broker.ip}\nECCI_LOCAL_BROKER_PORT={local_broker.port}\nECCI_LOCAL_BROKER_USERNAME=\nECCI_LOCAL_BROKER_PASSWORD=\nECCI_LOCAL_BROKER_ID={local_broker.id}\nECCI_MINIO_IP={local_broker.ip}\nECCI_MINIO_PORT=9000\nECCI_MINIO_ACCESS_KEY=\nECCI_MINIO_SECRET_KEY="
        filename = ".env"
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="{0}"'.format(filename)
        return response
        # return HttpResponse(content, content_type='text/plain')
    
filemanager_ENV_download_view = FileManagerENVDownloadAPIView.as_view()