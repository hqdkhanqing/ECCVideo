import os
from wsgiref.util import FileWrapper
from django.http import StreamingHttpResponse, Http404
from django.conf import settings
from django.contrib.auth.signals import user_logged_in
import datetime
import re, json
import time
import requests
from requests.auth import AuthBase
from requests.auth import HTTPBasicAuth
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.db.models import Sum
from django.utils.encoding import escape_uri_path
from furl import furl
from drf_signed_auth.signing import UserSigner
from drf_signed_auth import settings as signed_auth_settings
import paho.mqtt.client as mqtt
import pymongo

# 8-7 agent response received import
import paho.mqtt.subscribe as subscribe
from func_timeout import func_set_timeout
from func_timeout.exceptions import FunctionTimedOut

range_re = re.compile(r'bytes\s*=\s*(\d+)\s*-\s*(\d*)', re.I)

HTTP_METHODS = [
    'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE'
]

# timeout时间，用于func_set_timeout装饰器————实现Pub/Sub的同步
TIMEOUT_SETTING = 5

mqtt_ip = getattr(settings, 'MQTT_IP', None)

mqtt_port = getattr(settings, 'MQTT_PORT', None)


def sendfile(request, url, path, mime_type=None):
    MEDIA_USE_XSENDFILE = getattr(settings, 'MEDIA_USE_XSENDFILE', False)
    range_header = request.META.get('HTTP_RANGE', '').strip()
    range_match = range_re.match(range_header)
    size = os.path.getsize(path)
    content_type = mime_type or 'application/octet-stream'
    if MEDIA_USE_XSENDFILE:
        resp = StreamingHttpResponse(status=200)
        resp['Content-Type'] = content_type
        resp['X-Accel-Redirect'] = url
        resp['X-Sendfile'] = url
        resp['Content-Length'] = str(size)
    else:
        if range_match:
            first_byte, last_byte = range_match.groups()
            first_byte = int(first_byte) if first_byte else 0
            last_byte = int(last_byte) if last_byte else size - 1
            if last_byte >= size:
                last_byte = size - 1
            length = last_byte - first_byte + 1
            resp = StreamingHttpResponse(RangeFileWrapper(open(path, 'rb'),
                                                          offset=first_byte,
                                                          length=length),
                                         status=206,
                                         content_type=content_type)
            resp['Content-Length'] = str(length)
            resp['Content-Range'] = 'bytes %s-%s/%s' % (first_byte, last_byte,
                                                        size)
        else:
            resp = StreamingHttpResponse(FileWrapper(open(path, 'rb')),
                                         content_type=content_type)
            resp['Content-Length'] = str(size)
    return resp



def jwt_response_payload_handler(token, user=None, request=None):
    if user and request:
        user_logged_in.send(sender=user.__class__, request=request, user=user)
    return {
        'token': token,
    }


def get_signed_url(request, url):
    """
        Returns provided URL with an authentication
        signature.
        """
    signer = UserSigner()
    #url = request.build_absolute_uri(url)
    signature = signer.sign(user=request.user)
    param = signed_auth_settings.SIGNED_URL_QUERY_PARAM
    return furl(url).add({param: signature}).url


def pub_to_driver_program(topic, payload, timeoutFlag=True):
    client = mqtt.Client(client_id="app_control")
    client.connect(mqtt_ip, mqtt_port, 60)
    client.loop_start()
    client.publish(topic, payload, 2, retain=False)
    client.loop_stop()
    if timeoutFlag:
        try:
            msg = operateResponse(payload)
            return "response"
        except FunctionTimedOut:
            return "timeout"


# agent response received function
@func_set_timeout(TIMEOUT_SETTING)
def operateResponse(operateId):
    msg = subscribe.simple("res/app_manage_success/" + operateId,
                           hostname=mqtt_ip,
                           port=mqtt_port)
    return msg


def req_to_driver_program(logical_topology_id, payload, timeoutFlag=True):
    topic = 'req/app_manage/' + logical_topology_id + '/orchestrate'
    client = mqtt.Client(client_id="app_orchestrate")
    client.connect(mqtt_ip, mqtt_port, 60)
    client.loop_start()
    client.publish(topic, payload, 2, retain=False)
    client.loop_stop()
    if timeoutFlag:
        try:
            msg = orchestrateResponse(logical_topology_id)
            msg['status'] = 'successed'
            return msg
        except FunctionTimedOut:
            return {'status': 'failed'}


# agent response received function
@func_set_timeout(TIMEOUT_SETTING)
def orchestrateResponse(operateId):
    msg = subscribe.simple("res/app_manage_success/" + operateId,
                           hostname=mqtt_ip,
                           port=mqtt_port)
    return msg
