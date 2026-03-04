Voici **l’architecture finale RAG complète**, adaptée à :

* 📖 Bible
* 📿 Rosaire
* ⛪ Disponibilité prêtres / sœurs
* 🧠 Gemini (LLM + embeddings)
* 🗄 PostgreSQL + pgvector
* ⚡ Backend Django structuré

Architecture pensée pour :

* Robustesse
* Sécurité
* Scalabilité
* Raisonnement multi-domaines
* Zéro hallucination sur données horaires

---

# 🏗 ARCHITECTURE GLOBALE

```
                         ┌────────────────────┐
                         │     USER QUERY     │
                         └─────────┬──────────┘
                                   │
                                   ▼
                    ┌────────────────────────────┐
                    │  INTENT + ENTITY EXTRACTOR │
                    │      (Gemini small)        │
                    └─────────┬──────────────────┘
                              │
                              ▼
                     ┌───────────────────┐
                     │   QUERY ROUTER    │
                     └───────┬───────────┘
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌────────────────┐   ┌────────────────┐   ┌────────────────┐
│  BIBLE ENGINE  │   │ ROSARY ENGINE  │   │ AVAILABILITY   │
│ (Vector Search)│   │ (Vector + Rule)│   │ (SQL Service)  │
└────────┬───────┘   └────────┬───────┘   └────────┬───────┘
         │                    │                    │
         └──────────────┬─────┴──────────────┬─────┘
                        ▼                    ▼
                ┌──────────────────────────────────┐
                │        CONTEXT BUILDER           │
                └──────────────────────────────────┘
                                   │
                                   ▼
                        ┌────────────────────┐
                        │  GEMINI LLM FINAL  │
                        └────────────────────┘
                                   │
                                   ▼
                            FINAL RESPONSE
```

---

# 🧠 ÉTAPE 1 — INTENT + ENTITY EXTRACTION

Utiliser Gemini en mode **structured JSON output**.

Input :

> “Je veux un verset sur la miséricorde et savoir si un prêtre est disponible demain après 16h à Mbour.”

Output attendu :

```json
{
  "intent": "MIXED",
  "domains": ["BIBLE", "AVAILABILITY"],
  "entities": {
    "topic": "miséricorde",
    "date": "2026-03-02",
    "time_after": "16:00",
    "city": "Mbour",
    "service": null
  }
}
```

⚠️ Important :
Gemini ne génère PAS de SQL.
Il extrait uniquement des paramètres.

---

# 📖 BIBLE ENGINE

## Stockage

Table `bible_chunks` :

* id
* content
* book
* chapter
* verse
* testament
* embedding (pgvector)

## Pipeline

```
Query → Embedding Gemini → pgvector similarity search → Top K
```

Option hybride :

* PostgreSQL full-text search
* Puis vector rerank

---

# 📿 ROSARY ENGINE

Deux modes :

## 1️⃣ Mode logique simple

Si question :

> “Quel mystère aujourd’hui ?”

On utilise règle :

* Monday/Saturday → Joyeux
* Tuesday/Friday → Douloureux
* Wednesday/Sunday → Glorieux
* Thursday → Lumineux

Pas de vector search nécessaire.

---

## 2️⃣ Mode sémantique

Si question :

> “Mystère lié à la joie”

Vector search sur :

* Mysteries
* Méditations
* Prières

Table `rosary_chunks` :

* id
* type (mystery/prayer)
* group
* order
* content
* embedding

---

# ⛪ AVAILABILITY ENGINE

⚠️ Pas vectorisé.

Pipeline :

```
Extracted entities
     ↓
AvailabilityService
     ↓
Structured SQL
     ↓
Slots list
```

Jamais laisser le LLM toucher la base.

---

# 🏗 CONTEXT BUILDER

Structure finale envoyée au LLM :

```
{
  "bible_context": [...],
  "rosary_context": [...],
  "availability_context": [...]
}
```

Format clair :

```
=== BIBLICAL PASSAGES ===
Book: Luke 6:36
Text: ...

=== ROSARY ===
Mystery: L’Annonciation

=== AVAILABILITY ===
Père Jean – 16:00–18:00 – Paroisse St Paul
```

---

# 🤖 GEMINI FINAL GENERATION

Prompt système :

* Ne jamais inventer versets
* Ne jamais inventer horaires
* Répondre uniquement avec contexte fourni
* Structurer si question mixte

---

# 🗄 BASE DE DONNÉES

## PostgreSQL

Tables :

* bible_chunks
* rosary_chunks
* availability models
* embeddings stored via pgvector

Index :

* GIN full-text
* pgvector HNSW

---

# ⚡ CACHE LAYER

Redis :

* Bible top results (short TTL)
* Rosary day result
* Availability daily results

Ne pas cacher requêtes mixtes personnalisées.

---

# 🧠 ROUTING LOGIC

Pseudo-code :

```python
if intent == "BIBLE":
    bible_results = bible_engine.search(query)

elif intent == "ROSARY":
    rosary_results = rosary_engine.search(query)

elif intent == "AVAILABILITY":
    availability = availability_service.get_slots(entities)

elif intent == "MIXED":
    bible_results = ...
    availability = ...
    rosary_results = ...
```

---

# 🛡 SÉCURITÉ

Ne jamais :

* Injecter SQL généré
* Donner accès brut au LLM
* Laisser halluciner horaires

Toujours :

* Structurer
* Valider
* Injecter contexte limité

---

# 📊 PERFORMANCE

* Index vector HNSW
* Embeddings batch
* Top 5 max
* Limiter contexte tokens

---

# 🎯 CAPACITÉS FINALES

Ton assistant pourra :

✔ Donner un verset exact
✔ Recommander mystère correct
✔ Donner horaires précis
✔ Répondre multi-domaines
✔ Rester théologiquement cohérent
✔ Éviter hallucination

---

# 🧩 STRUCTURE TECHNIQUE DJANGO

Créer app :

```
rag/
    router.py
    extractor.py
    bible_engine.py
    rosary_engine.py
    availability_engine.py
    context_builder.py
    llm_client.py
    schemas.py
```

---