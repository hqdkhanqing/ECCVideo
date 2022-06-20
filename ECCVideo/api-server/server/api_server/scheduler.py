from apscheduler.schedulers.background import BackgroundScheduler
from api_server.tasks import MonitorData
from django.utils import timezone
from django.conf import settings

scheduler = BackgroundScheduler(timezone=timezone.get_current_timezone())


def cleanup_outdated_monitor_data():
    monitorData = MonitorData()
    monitorData.delete_container_data()
    monitorData.delete_device_data()

cron_minute= getattr(settings,'CLEANUP_OUTDATED_MONITORDATA_CRON_MINUTE',00)   
cron_hour= getattr(settings,'CLEANUP_OUTDATED_MONITORDATA_CRON_HOUR',00)
scheduler.add_job(cleanup_outdated_monitor_data, 'cron', hour=cron_hour,minute=cron_minute)
