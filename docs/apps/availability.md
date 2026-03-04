# Module Disponibilités (JanguBi)

## Présentation
Le module **Availability** permet la prise de rendez-vous avec les ministres ordonnés et consacrés (Prêtres, Diacres, Religieux, Sœurs, Évêques) rattachés à différentes paroisses.

## Fonctionnalités Principales
1. **Gestion Multi-Paroisses** : Un prêtre appartient à une paroisse, où il exerce ses services.
2. **Services Modulables** : Un administrateur peut créer différents services dotés de durées précises (Confession = 15m, Accompagnement = 45m).
3. **Moteur d'Agenda Avancé** : Le backend gère dynamiquement :
    - Les disponibilités régulières (ex: tous les lundis matin).
    - Les disponibilités exceptionnelles (ex: ce vendredi soir).
    - Les créneaux bloqués (ex: retraite spirituelle, maladie).
    - Les rendez-vous déjà confirmés (Bookings).
4. **Calcul de Créneaux Discrets** : Transforme une large plage (ex: 14h-17h) en petits créneaux cliquables de X minutes selon le service demandé, en filtrant les overlaps.

## Architecture
- **Modèles de Base** : `Parish`, `ServiceType`, `Minister`.
- **Modèles de Calendrier** : `WeeklyAvailability`, `SpecialAvailability`, `BlockedSlot`, `Booking`.
- **Service Métier** : `AvailabilityService` (dans `apps/availability/services.py`) est un algorithme puissant calculant à la volée le calendrier du mois et les créneaux libres en mémoire pure.
- **Cache Actif** : Les données renvoyées sont mises en cache Redis pour réduire la charge DB, avec invalidation dynamique par **Signaux Django** (`signals.py`) dès qu'une entité est mise à jour par l'admin.

## Endpoints API Clés
- `GET /api/v1/availability/parishes/` (et Admin CRUD).
- `GET /api/v1/availability/services/` (et Admin CRUD).
- `GET /api/v1/availability/ministers/` (et Admin CRUD).
- `GET /api/v1/availability/available/?date=...&service=...` : Retourne la liste des ministres dispo ce jour-là.
- `GET /api/v1/availability/ministers/<slug>/available/` : Retourne la liste exacte des heures pour un prêtre précis.
- `GET /api/v1/availability/calendar/<slug>/?month=YYYY-MM` : Génère le mois en code couleur.
