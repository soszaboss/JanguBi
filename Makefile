.PHONY: up down restart build logs shell dbshell makemigrations migrate check test init-data create-admin init-all

# ==============================================================================
# COMMANDES DOCKER
# ==============================================================================
up:
	docker compose up -d

down:
	docker compose down -v

restart:
	docker compose restart

build:
	docker compose build

logs:
	docker compose logs -f django

# ==============================================================================
# COMMANDES DJANGO (Méthode 1 / Manuel)
# ==============================================================================
shell:
	docker compose exec django python manage.py shell

dbshell:
	docker compose exec db psql -U postgres -d styleguide_example_db

makemigrations:
	docker compose exec django python manage.py makemigrations

migrate:
	docker compose exec django python manage.py migrate

check:
	docker compose exec django python manage.py check

test:
	docker compose exec django pytest

createsuperuser:
	docker compose exec django python manage.py createsuperuser

import-aelf:
	$(eval TODAY := $(shell date +%Y-%m-%d))
	docker compose exec django python manage.py import_aelf --start $(TODAY) --end $(TODAY)

clear-cache:
	docker compose exec django python manage.py shell -c "from django.core.cache import cache; cache.clear()"

flush-redis:
	docker compose exec redis redis-cli FLUSHALL

flush-db:
	docker compose exec django python manage.py flush --no-input

seed-availability:
	docker compose exec django python manage.py seed_availability

# ==============================================================================
# BIBLE & RAG UTILS
# ==============================================================================
check-embeddings:
	docker compose exec django python manage.py check_embeddings

seed-embeddings:
	docker compose exec django python manage.py shell -c "from apps.bible.models import Book; from apps.bible.tasks import compute_embeddings_task; [compute_embeddings_task.delay(b.id) for b in Book.objects.all()]; print('Dispatched embedding tasks for all books.')"

# ==============================================================================
# INFRASTRUCTURE & MAINTENANCE
# ==============================================================================
celery-logs:
	docker compose logs -f celery

celery-restart:
	docker compose restart celery

rabbitmq-stats:
	docker compose exec rabbitmq rabbitmqctl list_queues

clean-audio:
	docker compose exec django python manage.py shell -c "import os; from django.conf import settings; path = os.path.join(settings.MEDIA_ROOT, 'rosary'); [os.remove(os.path.join(path, f)) for f in os.listdir(path) if f.endswith('.mp3')]; print('Local audio cache cleaned.')"

# ==============================================================================
# INITIALISATION DU PROJET
# ==============================================================================
init-data:
	chmod +x ./scripts/init_bible_data.sh
	./scripts/init_bible_data.sh

create-admin:
	chmod +x ./scripts/create_admin.sh
	./scripts/create_admin.sh

init-all: init-data create-admin
