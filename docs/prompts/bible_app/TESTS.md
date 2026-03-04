
---

## 🎯 Objectif

Tu es un **Senior QA Engineer spécialisé Django + PostgreSQL + Celery**.

Tu dois écrire **tous les tests du module `bible`**.

Tu ne modifies pas le code métier.
Tu écris uniquement les tests.

Framework :

* pytest
* pytest-django
* pytest-asyncio (si nécessaire)
* factory_boy (si utile)
* unittest.mock / pytest-mock
* httpx mocking
* celery testing utilities

Couverture minimale exigée : **≥ 85% sur le module bible**

---

# 📦 1. TESTS D’INGESTION

## 1.1 Import JSON — Format A

Test :

* Import d’un extrait minimal du format :

  * Testaments → Books → Chapters → Verses
* Vérifier :

  * Testament créé
  * Book créé
  * Chapter créé
  * Verses créés
  * `number` commence à 1
  * `original_id` conservé si présent

Edge cases :

* Premier verset sans ID → doit être `number=1`
* Plusieurs versets sans ID → doivent être séquentiels
* Ordre conservé

---

## 1.2 Import JSON — Format B

Test :

* Format `books → chapters → verses`
* Vérifier :

  * Psaumes assigné à Ancien Testament
  * `verse_count` correct
  * `chapter.verse_count` correct

---

## 1.3 Nettoyage texte

Tester `clean_text()` avec :

Cas 1 :

```
"\\u00e9"
```

→ devient `"é"`

Cas 2 :

```
"&nbsp;Bonjour&nbsp;"
```

→ `"Bonjour"`

Cas 3 :
Caractères invisibles
→ supprimés

Cas 4 :
Double espaces
→ un seul espace

Cas 5 :
Guillemets typographiques
→ normalisés

---

## 1.4 Résolution du livre Psaumes

Test :

* "Psalms"
* "Psaume"
* "Psaumes"
* "PSALMS"

→ toujours assigné au Testament "ancien"

---

# 🔍 2. TESTS DE RECHERCHE

## 2.1 Recherche lexicale simple

Setup :

* Insérer verset connu : "Heureux l’homme..."

Test :

* `GET /api/search/?q=Heureux`
* Résultat :

  * Livre correct
  * Chapter correct
  * Verse correct
  * URL correcte
  * group_by=book respecté

---

## 2.2 Recherche groupée par livre

* Si 3 versets matchent dans 1 livre :

  * Résultat contient 1 livre
  * matches contient 3 versets

---

## 2.3 Test paramètre testament

* Recherche `?testament=ancien`
* Aucun verset du nouveau testament ne doit apparaître

---

## 2.4 Test hybrid search (si pgvector activé)

Mock embedding
Mock vector score

Test :

* hybrid_search combine scores correctement
* alpha weighting respecté
* si score < threshold → flag `no_internal_source=true`

---

# 🌐 3. TESTS API NAVIGATION

## 3.1 Liste des testaments

`GET /api/testaments/`

* retourne 2 éléments
* cache activé
* structure correcte

---

## 3.2 Liste des livres d’un testament

`GET /api/testaments/ancien/books/`

Vérifier :

* Pas de versets dans réponse
* Pas de chapitres
* verse_count présent
* payload léger

---

## 3.3 Détail d’un livre

`GET /api/books/{id}/`

Sans expand :

* Pas de chapitres

Avec `?expand=chapters` :

* Chapitres présents
* Pas de versets

---

## 3.4 Versets paginés

`GET /api/books/{book}/chapters/{n}/verses/`

* Pagination fonctionne
* excerpt fonctionne si `?excerpt=true`

---

# 🔁 4. TESTS CELERY

## 4.1 Import Task

* Mock import service
* Vérifier tâche exécutée
* Vérifier logs

---

## 4.2 Embedding Task

Mock provider embeddings

* Vérifier update `embedding`
* Vérifier batch handling

---

## 4.3 AELF Fetch Task

Mock httpx response

Test :

* DailyText créé
* Retry sur erreur
* Backoff respecté
* local_matches rempli si correspondance trouvée

---

# 🚀 5. TESTS PERFORMANCE

## 5.1 Bulk import 5 000 versets

* Temps < seuil acceptable (ex: <5s en test)
* Pas de duplication
* Nombre correct en base

---

## 5.2 Search performance

* Recherche < 300ms (mocked environment)

---

# 🔐 6. TESTS SÉCURITÉ

## 6.1 Import endpoint

* Non authentifié → 401
* Auth admin → 200

---

## 6.2 Injection SQL protection

Test :
`q="'; DROP TABLE bible_verse; --"`

* Pas d’erreur
* Pas de fail

---

# 🧠 7. TESTS AELF INTEGRATION

Mock réponses AELF :

Cas :

* Messe
* Heures
* Lecture

Vérifier :

* Catégorie correcte
* Date correcte
* Mapping vers versets fonctionne si texte correspond

---

# 📊 8. TESTS CACHE

Mock Redis

Test :

* Première requête → hit DB
* Deuxième requête → cache hit
* Import → cache invalidé

---

# 🧪 9. TESTS EDGE CASES

* Chapitre sans versets
* Livre sans chapitres
* Fichier JSON vide
* Fichier JSON malformé
* Doublon import
* Caractères Unicode rares

---

# 🧾 STRUCTURE DES TESTS ATTENDUE

```
tests/
 ├── test_cleaning.py
 ├── test_import_format_a.py
 ├── test_import_format_b.py
 ├── test_book_mapping.py
 ├── test_api_navigation.py
 ├── test_search.py
 ├── test_hybrid_search.py
 ├── test_celery_tasks.py
 ├── test_aelf_integration.py
 ├── test_cache.py
 ├── test_security.py
```

---

# 📌 Contraintes supplémentaires

* Tous les appels externes doivent être mockés
* Les tests doivent être indépendants
* Utiliser fixtures pytest
* Ne jamais dépendre d’une base réelle
* Tests doivent passer en CI sans GPU
* Embeddings doivent être mockés

---

# 🎯 Résultat attendu

À la fin :

* Tous les tests passent
* Coverage ≥ 85%
* Aucun test flaky
* Documentation des tests claire
* CI ready

---