#!/bin/bash
set -a
# Charger les variables du .env si existant
[ -f .env ] && source .env
set +a

echo "==========================================================="
echo "   Initialisation de la base de données Bible"
echo "==========================================================="

echo "1. Application des migrations Django..."
docker compose exec django python manage.py migrate

echo "2. Importation du format A (bible-fr.json)..."
# On ignore les erreurs potentielles de doublons si déjà run
docker compose exec django python manage.py import_bible init/bibles/format/json/bible-fr.json --source bible_fr

echo "3. Importation du format B (FreSynodale1921.json)..."
docker compose exec django python manage.py import_bible init/bibles/format/json/FreSynodale1921.json --source FreSynodale1921

echo "4. Exécution du script conditionnel pgvector..."
docker compose exec -T db psql -U postgres -d styleguide_example_db < init/postgresql/pgvector_conditional.sql

echo "5. Création et configuration du bucket MinIO pour les audios..."
docker compose exec minio sh -c 'mc alias set local http://localhost:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD && mc mb local/rosary-audio || true && mc anonymous set public local/rosary-audio'

echo "6. Importation des données du Rosaire..."
docker compose exec django python manage.py seed_rosary

echo "7. Importation de la liturgie du jour (AELF)..."
TODAY=$(date +%Y-%m-%d)
docker compose exec django python manage.py import_aelf --start $TODAY --end $TODAY

echo "==========================================================="
echo "   Importation et Indexation terminées !"
echo "==========================================================="
