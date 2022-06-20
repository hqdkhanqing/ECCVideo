import os
from datetime import datetime,timedelta
from .models import ContainerData,DeviceData


class MonitorData:
    def delete_container_data(self):
        container_datas = ContainerData.objects.filter(timestamp__lt = datetime.today() + timedelta(-1))
        container_datas.delete()

    def delete_device_data(self):
        device_datas = DeviceData.objects.filter(timestamp__lt = datetime.today() + timedelta(-1))
        device_datas.delete()