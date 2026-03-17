"""
Celery configuration for speech_therapy project.
"""
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "speech_therapy.settings")

app = Celery("speech_therapy")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
