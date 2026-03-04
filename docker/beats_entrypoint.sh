#!/bin/bash
echo "--> Starting beats process"
celery -A apps.tasks beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
