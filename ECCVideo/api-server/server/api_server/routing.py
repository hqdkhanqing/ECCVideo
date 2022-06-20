from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/orchestrator/$', consumers.OrchestratorConsumer),
    re_path(r'ws/controller/$', consumers.ControllerConsumer),
    re_path(r'ws/monitor/$', consumers.MonitorConsumer),
]