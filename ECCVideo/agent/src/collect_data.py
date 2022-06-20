import re
import json
import psutil
import subprocess
import time
import docker
import platform
import socket
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#采集主机监控信息
def get_host_info(deviceID):
    host_info = dict()
    host_info['device'] = deviceID
    host_info['cpu_count'] = str(psutil.cpu_count())
    host_info['cpu_usage'] = "%0.2f"%psutil.cpu_percent(interval=1, percpu=False)+"%"
    mem = psutil.virtual_memory()
    host_info['mem_size'] = str(int(mem.total / (1024 ** 2)))
    host_info['mem_usage'] = str(int(mem.used / (1024 ** 2)))
    host_info['net_in'] = str(psutil.net_io_counters().bytes_recv)
    host_info['net_out'] = str(psutil.net_io_counters().bytes_sent)
    host_info['timestamp'] = time.strftime("%Y-%m-%dT%H:%M:%S",time.localtime(time.time()))
    return host_info

# 采集容器数据
def get_container_info(deviceID):
    client = docker.from_env()
    oldclient = docker.APIClient(base_url='unix://var/run/docker.sock')
    # oldAPIClient = docker.APIClient(base_url='unix://var/run/docker.sock')
    container_info_array = []
    container_status_array = []
    for container in client.containers.list(all=True, filters={"name":"edgeai"}):
        try:
            container_info = {}
            container_status_info = {}
            (app_id, container_name) = re.findall(r"^edgeai_(.*?)_(.*)", container.name)[0]
            
            container_status_info['app_id'] = app_id
            container_status_info['container_name'] = container_name
            container_status_info['status'] = container.status
            container_status_info["agent_id"] = deviceID

            container_info['container_name'] = container_name
            container_info['app'] = app_id
            container_info['device'] = deviceID
            stats = container.stats(stream=False)
            container_info['mem_usage'] = str(stats['memory_stats']['usage'])
            container_info['mem_percent'] = '%.2f%%'%((stats['memory_stats']['usage']/stats['memory_stats']['limit'])*100)
            container_info['net_in'] = str(list(stats['networks'].values())[0]['rx_bytes'])
            container_info['net_out'] = str(list(stats['networks'].values())[0]['tx_bytes'])
            total_usage = stats['cpu_stats']['cpu_usage']['total_usage']
            previous_total_usage = stats['precpu_stats']['cpu_usage']['total_usage']
            system_usage = stats['cpu_stats']['system_cpu_usage']
            previous_system_usage = stats['precpu_stats']['system_cpu_usage']
            percpu_num = len(stats['cpu_stats']['cpu_usage']['percpu_usage'])
            cpu_delta = total_usage - previous_total_usage
            system_delta = system_usage - previous_system_usage
            container_info['cpu_usage'] = '%.2f%%'%((cpu_delta/system_delta)*percpu_num)
            container_info['timestamp'] = time.strftime("%Y-%m-%dT%H:%M:%S",time.localtime(time.time()))
            container_info['image_name'] = container.image.tags[0]
            container_info['status'] = container.status
            container_info['create_at'] = oldclient.inspect_container(container.id)['Created']
            container_info['platform'] = oldclient.inspect_container(container.id)['Platform']
            container_info_array.append(container_info)
            container_status_array.append(container_status_info)
        except IndexError:
            pass
        except KeyError:
            container_status_array.append(container_status_info)
        except Exception as e:
            logger.error(e)

    return container_info_array,container_status_array

def get_device_info():
    device_info = dict()
    device_info['os'] = platform.platform()
    device_info['name'] = platform.node()
    device_info['ip'] = socket.gethostbyname(socket.gethostname())
    client = docker.from_env()
    device_info['docker_version'] = client.version()['Version']
    device_info['cpu_cores'] = psutil.cpu_count()
    device_info['memory'] = int(psutil.virtual_memory().total / (1024 ** 2))
    return device_info

