from celery import Celery
from celery.schedules import crontab

app = Celery('Dispencer')

app.conf.beat_schedule = {
    'update-device-status-every-minute': {
        'task': 'dashboard.tasks.update_device_status',
        'schedule': crontab(minute='*/1'),
    },
}
