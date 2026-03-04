
---

# 📌 PROMPT

---

## 🎯 CONTEXTE PROJET

Nous développons un module `rosary` dans une application Django + PostgreSQL.

Nous avons un fichier :

```
rosary_french.json
```

Structure :

* Intro
* Mysteries (5)
* Closing
* Group (Joyful / Sorrowful / Glorious / Luminous)
* Day

Nous voulons :

1. Normaliser les données
2. Stocker proprement en base
3. Relier chaque mystère à un audio stocké sur MinIO
4. Exposer une API REST propre
5. Préparer la base pour RAG futur
6. Optimiser les requêtes (pas de surcharge inutile)

---

# 📦 ARCHITECTURE ATTENDUE

App Django :

```
rosary/
    models.py
    serializers.py
    services.py
    views.py
    urls.py
    tasks.py
    storage.py
    management/commands/seed_rosary.py
```

---

# 🧱 MODÈLES À GÉNÉRER

### 1️⃣ MysteryGroup

* id
* name (unique)
* slug
* created_at

---

### 2️⃣ Mystery

* id
* group (FK → MysteryGroup)
* order (1-5)
* title
* audio_file (MinIO URL)
* audio_duration (optional)
* created_at

Constraint :

```
unique_together = (group, order)
```

---

### 3️⃣ Prayer

* id
* type (ENUM)
* text
* language (FR default)
* embedding (VectorField nullable, pour futur RAG)
* created_at

Enum types :

* SIGN_OF_CROSS
* CREED
* OUR_FATHER
* HAIL_MARY
* GLORY_BE
* FATIMA
* HOLY_QUEEN
* FINAL_PRAYER

---

### 4️⃣ MysteryPrayer

Relation ManyToMany intermédiaire :

* mystery (FK)
* prayer (FK)
* order (int)

---

### 5️⃣ RosaryDay

* id
* weekday (ENUM)
* group (FK)
* created_at

---

# 🔊 MINIO CONFIGURATION

Utiliser `django-storages` compatible S3.

Créer :

```
storage.py
```

Avec :

* S3Boto3Storage custom
* bucket_name = "rosary-audio"
* file_overwrite = False
* default_acl = private

Les audios sont uploadés manuellement.
Chaque mystère doit avoir :

```
audio_file = models.FileField(storage=MinioStorage)
```

---

# 📜 SCRIPT D’INITIALISATION

Créer management command :

```
python manage.py seed_rosary
```

Fonctions :

1. Lire `rosary_french.json`
2. Créer groupes
3. Créer mystères
4. Créer prières dédupliquées
5. Relier via MysteryPrayer
6. Ne jamais recréer si existant (idempotent)

---

# 🧠 SERVICES À CRÉER

### RosaryService

Méthodes :

* get_groups()
* get_group_with_mysteries(group_slug, include_prayers=False)
* get_day_rosary(weekday)
* search_text(query)
* vector_search(query, embedding=None)

Optimisation :

* select_related
* prefetched_related
* annotations

---

# 🔌 SERIALIZERS

### GroupSerializer

Sans mystères par défaut.

### MysterySerializer

Option :

```
?include_prayers=true
```

### RosaryDaySerializer

Retour :

* group
* mysteries (sans prières sauf si demandé)

---

# 🌐 URL STRUCTURE OBLIGATOIRE

Tu dois respecter strictement ceci :

```
/api/rosary/groups/
/api/rosary/groups/{slug}/
/api/rosary/groups/{slug}/mysteries/
/api/rosary/mysteries/{id}/
/api/rosary/days/{weekday}/
/api/rosary/search/?q=
/api/rosary/vector-search/
```

Important :

* Les endpoints groupes ne doivent pas charger les prières par défaut.
* Pas de nested lourd.
* Ajouter pagination si nécessaire.

---

# 🔎 RECHERCHE TEXTUELLE

Utiliser PostgreSQL full-text search.

Créer :

* index GIN
* SearchVector sur Prayer.text

Endpoint :

```
/api/rosary/search/?q=miséricorde
```

Retour :

* mystère
* extrait
* score
* lien vers mystère

---

# 🧠 RECHERCHE VECTORIELLE (FUTUR)

Prévoir champ :

```
embedding = VectorField(dimensions=768, null=True)
```

Créer service stub :

```
vector_search(query)
```

Sans implémentation obligatoire maintenant.

---

# ⚡ CACHE

Utiliser Redis.

Mettre en cache :

* groups list (24h)
* mysteries by group (12h)
* rosary by weekday (6h)

Ne pas mettre en cache recherche.

---

# 🧪 CONTRAINTES

* Code propre
* Typing Python
* Query optimisée
* Aucune requête N+1
* Tests possibles ultérieurement
* Séparation logique claire (services != views)

---

# 🎯 BONUS

Ajouter :

```
/api/rosary/today/
```

Qui retourne automatiquement le mystère du jour selon logique catholique standard :

* Monday/Saturday → Joyful
* Tuesday/Friday → Sorrowful
* Wednesday/Sunday → Glorious
* Thursday → Luminous

---

# ⚠️ INTERDIT

* Logique métier dans views
* Import direct JSON dans models
* Code dupliqué
* Hardcoding audio URLs

---

# 🎯 OBJECTIF FINAL

Obtenir un module rosary :

✔ Propre
✔ Normalisé
✔ Optimisé
✔ Compatible MinIO
✔ Prêt RAG
✔ Extensible
✔ Stable

---

Si tu veux, prochaine étape :

* Prompt pour agent TEST
* Prompt pour module Bible
* Prompt pour optimisation RAG
* Architecture microservice séparée

Choisis la suite.
