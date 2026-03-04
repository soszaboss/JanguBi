#!/bin/sh

# On affiche un message dans les logs
echo "🔄 Application des migrations de la base de données..."

# On lance les migrations
python manage.py migrate

# On exécute la commande passée dans le docker-compose (runserver)
echo "🚀 Démarrage du serveur..."
exec "$@"
