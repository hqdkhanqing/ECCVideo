from rest_framework import routers
from django.urls import re_path,path
from rest_framework_jwt.views import obtain_jwt_token,verify_jwt_token

from .views import AppViewSet, AgentViewSet, UserViewSet, ContainerDataViewSet, AgentDataViewSet,\
     OrchestrationViewSet, BrokerViewSet, AppContainerLogViewSet, RegistryViewSet, ContainerStatusViewSet, BrokerMonitorViewSet # AppDeployedViewSet,
from .views import app_download_view,RevokeJSONWebToken,agent_ENV_download_view,broker_ENV_download_view,usermonitor_ENV_download_view,filemanager_ENV_download_view

from django.conf.urls import url
from django.contrib import admin

router = routers.DefaultRouter()
router.register('apps', AppViewSet)
router.register('agents',AgentViewSet)
router.register('orchestrations',OrchestrationViewSet)
router.register('users',UserViewSet)
router.register('containers/Statistics', ContainerDataViewSet)
router.register('agentData', AgentDataViewSet)
router.register('appContainerLog', AppContainerLogViewSet)
router.register('brokers', BrokerViewSet)
router.register('brokerMonitors', BrokerMonitorViewSet)
# router.register('logicalTopologies', LogicalTopologyViewSet)
router.register('registry', RegistryViewSet)
router.register('containers/Status', ContainerStatusViewSet)

urlpatterns = router.urls+[
    path('apps/<str:pk>/download/<str:filename>',app_download_view,name='apps-download'),
    # path('logicalTopologies/<uuid:pk>/download/<str:filename>',logical_topology_download_view,name='logical_topologies-download'),
    path('auth/login/',obtain_jwt_token),
    path('auth/verify/',verify_jwt_token),
    path('auth/logout/',RevokeJSONWebToken.as_view()),
    path('agents/<str:pk>/download',agent_ENV_download_view, name="agent-env-download"),
    path('brokers/<str:pk>/download',broker_ENV_download_view, name="broker-env-download"),
    path('usermonitor/<str:pk>/download',usermonitor_ENV_download_view, name="usermonitor-env-download"),
    path('filemanager/<str:pk>/download',filemanager_ENV_download_view, name="filemanager-env-download"),
]
