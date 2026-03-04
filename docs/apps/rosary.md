# Module Rosaire (JanguBi)

## Présentation
Le module **Rosaire** permet aux fidèles d'être accompagnés dans la prière quotidienne du Rosaire. Il structure la prière par mystères et relie des fichiers audios hébergés en externe.

## Fonctionnalités Principales
1. **Groupe de Mystères** : Joyeux, Lumineux, Douloureux, Glorieux.
2. **Attribution Journalière** : Gère automatiquement le mystère du jour (ex: Lundi = Joyeux).
3. **Prière Guidée** : Chaque mystère est composé séquenciellement (Notre Père, 10 Je Vous Salue Marie, etc.).
4. **Hébergement Audio** : Connecté à MinIO/AWS S3 pour distribuer des enregistrements vocaux.

## Architecture
- **Modèles** : `MysteryGroup`, `Mystery`, `Prayer`, `RosaryDay`, `MysteryPrayer` (Table de liaison avec ordre).
- **Hébergement** : Configuration `storage.py` connectée à S3 pour le champ `audio_file` sur `MysteryGroup`.
- **Données Initiales** : La commande `python manage.py seed_rosary` parse un fichier JSON complexe, s'assure de l'idempotence, et upload les audios sur MinIO.

## Endpoints API Clés
- `GET /api/v1/rosary/today/` : Raccourci intelligent pour la page d'accueil (Le mystère du jour).
- `GET /api/v1/rosary/mysteries/<id>/` : Retourne la séquence parfaite pour le mode lecture / prière.
