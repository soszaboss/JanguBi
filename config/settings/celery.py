from config.env import env

# https://docs.celeryproject.org/en/stable/userguide/configuration.html

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="amqp://guest:guest@localhost//")
CELERY_RESULT_BACKEND = "django-db"

# Désactiver les heartbeats pour éviter "Too many heartbeats missed"
# lors des tâches longues et bloquantes (ex: import Bible) sur un worker mono-thread
CELERY_BROKER_HEARTBEAT = 0

CELERY_TIMEZONE = "UTC"

CELERY_TASK_SOFT_TIME_LIMIT = 1200  # 20 minutes
CELERY_TASK_TIME_LIMIT = 1800  # 30 minutes
CELERY_TASK_MAX_RETRIES = 3
