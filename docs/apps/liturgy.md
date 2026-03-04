# Module Liturgie (AELF) (JanguBi)

## Présentation
Le module **Liturgie** connecte JanguBi aux données de l'AELF (Association Épiscopale Liturgique pour les pays Francophones). Il récupère les textes des lectures des messes et des offices quotidiens.

## Fonctionnalités Principales
1. **Synchronisation Automatique** : Tâche de fond récupérant chaque jour les textes officiels pour la messe, les laudes, les vêpres, etc.
2. **Client HTTP Robuste** : Utilisation de `httpx` asynchrone avec gestion des retries (Tenacity) et limitation de cadence via Semaphores.
3. **Mapping Biblique (Matching)** : Fonctionnalité avancée où le code essaie de faire correspondre la référence AELF pure (ex: *Ps 22, 1-3*) vers nos ID de versets en base locale pour offrir une navigation enrichie.

## Architecture
- **Modèles** : `AelfDataEntry` (stockage brut), `LiturgicalDate`, `Office`, `Reading` (Relation).
- **Service** : L'`AelfService` agit comme Gateway/Facade.
- **Tâches Celery** : `daily_sync_aelf` est programmée dans Beat pour tourner à 2h00 du matin.

## Endpoints API Clés
- `GET /api/v1/liturgy/daily-office/?target_date=YYYY-MM-DD&office_type=messes` : Point d'entrée pour récupérer le texte liturgique mis en forme.
