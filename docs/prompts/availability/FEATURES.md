---

# 📌 PROMPT

---

## 🎯 CONTEXTE PROJET

Nous développons une application Django + PostgreSQL.

Nous devons créer un module `availability` permettant :

* Gestion des prêtres, sœurs, religieux
* Gestion des paroisses
* Gestion des disponibilités hebdomadaires
* Gestion des disponibilités exceptionnelles
* Gestion des indisponibilités
* Consultation publique des créneaux disponibles
* Préparation future pour réservation

Le code doit être :

* Propre
* Typé
* Optimisé
* Sans N+1
* Séparé (services != views)
* Prêt pour montée en charge

---

# 📦 ARCHITECTURE OBLIGATOIRE

Créer une app Django :

```
availability/
    models.py
    serializers.py
    services.py
    views.py
    urls.py
    filters.py
    permissions.py
    tasks.py
```

Ne pas mettre de logique métier dans les views.

---

# 🧱 MODÈLES À CRÉER

---

## 1️⃣ Parish

Champs :

* id
* name (unique)
* slug (unique)
* address
* city
* country
* latitude (DecimalField nullable)
* longitude (DecimalField nullable)
* is_active (bool)
* created_at
* updated_at

Index :

* city
* slug

---

## 2️⃣ Minister

Représente prêtre / sœur / religieux.

Champs :

* id
* first_name
* last_name
* slug (unique)
* photo (ImageField nullable)
* role (ENUM)
* parish (FK → Parish, related_name="ministers")
* bio (TextField)
* is_active (bool)
* created_at
* updated_at

Enum ROLE :

* PRIEST
* SISTER
* DEACON
* RELIGIOUS
* BISHOP

Index composite :

(role, parish)

---

## 3️⃣ ServiceType

Champs :

* id
* name (unique)
* slug (unique)
* description
* duration_minutes (PositiveIntegerField)
* is_active
* created_at

Exemples :

* Confession
* Direction spirituelle
* Accompagnement
* Entretien pastoral

---

## 4️⃣ WeeklyAvailability

Disponibilité récurrente.

Champs :

* id
* minister (FK → Minister, related_name="weekly_availabilities")
* weekday (IntegerField 0=Monday)
* start_time (TimeField)
* end_time (TimeField)
* service_type (FK → ServiceType)
* is_active
* created_at

Contraintes :

* start_time < end_time
* unique_together = (minister, weekday, start_time, end_time, service_type)

Index :

(minister, weekday)

---

## 5️⃣ SpecialAvailability

Disponibilité exceptionnelle.

Champs :

* id
* minister
* date (DateField)
* start_time
* end_time
* service_type
* created_at

---

## 6️⃣ BlockedSlot

Indisponibilité.

Champs :

* id
* minister
* date
* start_time
* end_time
* reason
* created_at

---

## 7️⃣ Booking (Préparation future)

Champs :

* id
* minister
* service_type
* date
* start_time
* end_time
* status (ENUM)
* created_at

Enum STATUS :

* PENDING
* CONFIRMED
* CANCELLED

---

# 🧠 SERVICES À IMPLÉMENTER

Créer `AvailabilityService` dans services.py.

Méthodes obligatoires :

### 1️⃣ get_available_slots(minister_slug, date)

Algorithme :

1. Charger WeeklyAvailability correspondant au weekday
2. Ajouter SpecialAvailability si existant
3. Retirer BlockedSlot
4. Retirer Booking CONFIRMED
5. Découper créneaux selon duration_minutes du ServiceType
6. Retourner liste des slots disponibles

---

### 2️⃣ get_available_ministers(date, service_slug)

Retourne :

* Liste des ministres ayant au moins un slot libre

---

### 3️⃣ compute_month_calendar(minister_slug, month)

Retour :

```
{
  "available_days": [],
  "full_days": [],
  "partial_days": []
}
```

---

Important :

* Utiliser select_related
* Utiliser prefetch_related
* Pas de requêtes dans boucle

---

# 🔌 SERIALIZERS

Créer :

### ParishSerializer

Sans ministres par défaut.

---

### MinisterListSerializer

Sans disponibilités.

---

### MinisterDetailSerializer

Option query param :

```
?include_availability=true
```

---

### SlotSerializer

Structure :

```
{
  "start": "09:00",
  "end": "09:30",
  "service": "confession"
}
```

---

# 🌐 STRUCTURE DES URLS (OBLIGATOIRE)

Respecter strictement :

```
/api/availability/parishes/
/api/availability/parishes/{slug}/

/api/availability/ministers/
/api/availability/ministers/{slug}/

/api/availability/ministers/{slug}/weekly/
/api/availability/ministers/{slug}/available/?date=YYYY-MM-DD

/api/availability/available/?date=YYYY-MM-DD&service=confession

/api/availability/calendar/{slug}/?month=YYYY-MM
```

Important :

* Pas de nested inutile
* Pagination sur listes
* Query params validés

---

# 🔐 PERMISSIONS

Créer permissions.py :

* Admin → CRUD complet
* Minister → modifier uniquement ses disponibilités
* Public → lecture seule

Utiliser DRF permissions propres.

---

# ⚡ CACHE STRATÉGIE

Utiliser Redis.

Mettre en cache :

* Parishes list (24h)
* Ministers list (12h)
* Weekly pattern (6h)

Ne pas mettre en cache :

* Slots du jour
* Recherche dynamique

---

# 📊 OPTIMISATION

Créer index :

* minister + weekday
* minister + date
* service_type

Ajouter validation pour :

* Chevauchement de créneaux
* start_time < end_time

---

# 🧪 PRÉPARATION POUR TESTS

Le code doit permettre :

* Test génération slot
* Test blocage
* Test conflit
* Test performance
* Test permissions

Ne pas écrire les tests maintenant.

---

# ⚠️ INTERDIT

* Logique métier dans views
* Boucle DB N+1
* Hardcoding horaires
* Mélange serializer/service

---

# 🎯 OBJECTIF FINAL

Un module :

✔ Propre
✔ Optimisé
✔ Extensible
✔ Multi-paroisse
✔ Compatible mobile
✔ Prêt pour réservation
✔ Haute cohérence métier

---

Si tu veux maintenant :

* Prompt pour agent TEST complet
* Version avec WebSocket temps réel
* Version multi-diocèse (multi-tenant)
* Diagramme ER détaillé

Choisis la suite.
