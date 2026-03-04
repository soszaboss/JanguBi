#!/bin/bash
set -a
# Charger les variables du .env si existant
[ -f .env ] && source .env
set +a

echo "==========================================================="
echo "   Création du Super Administrateur"
echo "==========================================================="

if [ -z "$ADMIN_EMAIL" ] || [ -z "$ADMIN_PASSWORD" ]; then
    echo "Erreur : Les variables d'environnement ADMIN_EMAIL et ADMIN_PASSWORD doivent être définies."
    echo "Veuillez les ajouter à votre fichier .env :"
    echo "ADMIN_EMAIL=admin@email.com"
    echo "ADMIN_PASSWORD=p@ss0rdH@shed"
    exit 1
fi

echo "Exécution de la commande sur le container Django..."
# On passe explicitement les variables d'environnement au cas où docker-compose ne les charge pas automatiquement du même shell
docker compose exec -T -e ADMIN_EMAIL="$ADMIN_EMAIL" -e ADMIN_PASSWORD="$ADMIN_PASSWORD" django python manage.py init_admin
