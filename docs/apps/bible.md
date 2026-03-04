# Module Bible (JanguBi)

## Présentation
Le module **Bible** est au cœur de l'application JanguBi. Il stocke, indexe et permet la consultation de l'intégralité des écritures saintes (Ancien et Nouveau Testament).

## Fonctionnalités Principales
1. **Consultation Hiérarchique** : Naviguer de Testament ➔ Livre ➔ Chapitre ➔ Versets.
2. **Recherche Full-Text (FTS)** : Recherche ultra-rapide par mots-clés via PostgreSQL `SearchVector`.
3. **Recherche Sémantique (Vectorielle / IA)** : Utilisation de **pgvector** et des **Embeddings Gemini** pour trouver des versets par le *sens* et non seulement par les mots exacts (ex: "J'ai peur de demain").

## Architecture
- **Modèles** : `Testament`, `Book`, `Chapter`, `Verse`.
- **Champs Spécifiques** :
  - `Verse.search_vector` : Index PostgreSQL FTS.
  - `Verse.embedding` : Vecteur mathématique à 768 dimensions (pgvector) représentant le sens de la phrase.
- **Services** : `SearchService` (dans `apps/bible/services/search_service.py`) orchestre la recherche en fusionnant (Hybrid Search) les scores FTS et Vectoriels.

## Endpoints API Clés
- `GET /api/v1/bible/testaments/` : Liste exhaustive pour le menu.
- `GET /api/v1/bible/books/` : Liste des livres (filtrable).
- `GET /api/v1/bible/books/<id>/chapters/<num>/verses/` : Lecture classique (paginée).
- `GET /api/v1/bible/search/?q=...&hybrid=true` : Moteur de recherche unifié.
