
---

# INSTRUCTIONS GÉNÉRALES

Objectif : implémenter un module Django nommé `bible` qui permet d’ingérer les fichiers JSON fournis, nettoyer et normaliser les données, stocker en Postgres (schéma fourni), exposer une API REST (DRF) pour navigation et recherche, calculer/populer un index full-text (tsvector) et préparer la colonne `embedding` (pgvector) pour RAG futur. Intégrer une ingestion asynchrone des **textes du jour / messe / heures** depuis l’API AELF, planifier la périodicité via Celery-beat, et prévoir la mise en cache Redis pour endpoints lourds.

Livrables attendus (fichiers et artefacts) :

* Django app `bible/` complète (models, serializers, views, urls, tests).
* Management command `import_bible` capable d’importer les deux formats JSON et corriger ID manquants.
* Services (Python) : `ImportService`, `CleaningService`, `IndexService`, `EmbeddingService` (stub), `SearchService`, `AELFService`.
* Celery tasks et Celery-beat schedule (fetch AELF daily).
* Docker Compose (Postgres, Redis, Django, Celery worker, Celery beat).
* SQL scripts pour index HNSW pgvector + GIN tsv.
* Tests unitaires et d’intégration (pytest + django).
* Documentation README : comment lancer, variables d’environnement, endpoints, exemples de payloads, critères d’acceptation.
* Fixtures de test (petit extrait JSON).

---

# DÉTAIL TECHNIQUE (ce que tu dois coder)

## 1. Stack et dépendances

* Python 3.12
* Django 5.2, Django REST Framework
* PostgreSQL (>=17) + extension `pgvector` (si disponible)
* `django-pgvector` (ou champ VectorField custom)
* `django-redis`
* Celery + Redis broker / backend
* httpx (async calls)
* pytest, pytest-django
* optional : `transformers`, `sentence-transformers` (pour embeddings local)
* Docker & docker-compose

## 2. Schéma de données (Django models)

Implémenter exactement les modèles suivants :

```python
# bible/models.py

class Testament(models.Model):
    slug = models.SlugField(max_length=32, unique=True)   # 'ancien' / 'nouveau'
    name = models.CharField(max_length=200)
    order = models.IntegerField(default=0)

class Book(models.Model):
    testament = models.ForeignKey(Testament, on_delete=models.PROTECT, related_name='books')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    alt_names = models.JSONField(default=list)  # alias
    order = models.IntegerField()
    verse_count = models.IntegerField(default=0)

class Chapter(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='chapters')
    number = models.IntegerField()
    name = models.CharField(max_length=255, blank=True)
    verse_count = models.IntegerField(default=0)

    class Meta:
        unique_together = ('book','number')

class Verse(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='verses')
    number = models.IntegerField()        # numéro dans le chapitre (1..n)
    text = models.TextField()
    original_id = models.IntegerField(null=True, blank=True)
    original_position = models.IntegerField(null=True, blank=True)
    source_file = models.CharField(max_length=128, blank=True, null=True)
    tsv = SearchVectorField(null=True)   # Postgres full-text
    embedding = VectorField(dimensions=1536, null=True, blank=True)  # pgvector
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('chapter','number')
        indexes = [ GinIndex(fields=['tsv']) ]
```

Notes :

* `VectorField` : utiliser `django-pgvector` if available. Si pgvector absent en dev, implementer champ stub (JSON) et documenter migration.
* Créer une table `DailyText` pour textes du jour :

```python
class DailyText(models.Model):
    date = models.DateField(db_index=True)
    category = models.CharField(max_length=64)  # 'messe', 'heures', 'lecture'
    title = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    source_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

## 3. Management command `import_bible` (import et nettoyage)

* Path : `bible/management/commands/import_bible.py`
* Usage : `python manage.py import_bible /path/to/file.json --source=FreSynodale1921`
* Fonctionnalités :

  1. Détecter format A (Testaments→Books→Chapters→Verses) ou format B (`books` list).
  2. For each book, resolve canonical name via `book_mapping.yaml` (voir section mapping). If book name matches Psalms/Psaumes, assign `testament.slug='ancien'`.
  3. For each chapter:

     * Build `verses_list` preserving order.
     * If verse dict lacks `ID` for first items, set `number` sequentially starting at 1.
     * Save original raw `ID` to `original_id` (may be null) and `original_position` = position in file (starting 1).
     * Clean text using `CleaningService.clean_text`
  4. Bulk insert `Book`, `Chapter`, `Verse` in chunks (batch size default 1000).
  5. After import, schedule tasks:

     * `index_service.populate_tsv_for_book(book_id)`
     * `embedding_service.enqueue_compute_embeddings_for_book(book_id)` (Celery)
  6. Log counts and errors; on error, rollback current book import and report.

### Cleaning rules (must be implemented in CleaningService)

* Decode double-escaped unicode: handle `\\u00e9` → `é` via `.encode('utf-8').decode('unicode_escape')` safely.
* Use `html.unescape` to decode `&amp;`, `&nbsp;`, etc.
* Remove control chars `[\x00-\x1F\x7F]`.
* Normalize whitespace to single spaces; trim.
* Normalize quotes: convert `’` and `“` to `'` and `"` if needed.
* Preserve original punctuation but canonicalize apostrophes.
* Return trimmed UTF-8 string.

## 4. Book mapping & Psalms

* Add `data/book_mapping.yaml` with canonical names and aliases. Example entry:

```yaml
Psaumes:
  canonical_name: "Psaumes"
  aliases: ["Psalms","Psalm","Psaume","Psalms (KJV)"]
  testament: "ancien"
  order: 19
```

* `ImportService.resolve_book(name)` must match aliases case-insensitively. If match not found, fallback: heuristics (if name contains 'psalm' or 'psaume') → assign Psalms to Ancien Testament.

## 5. Indexation full-text (tsvector) & SQL index

* After ingestion (per book), run:

```sql
UPDATE bible_verse SET tsv = to_tsvector('french', text) WHERE source_file = 'FreSynodale1921' AND book_id = <book_id>;
CREATE INDEX IF NOT EXISTS idx_verse_tsv ON bible_verse USING gin(tsv);
```

* If pg_trgm useful, create trigram index for partial matches:

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX IF NOT EXISTS idx_verse_text_trgm ON bible_verse USING gin (text gin_trgm_ops);
```

## 6. pgvector index (prévoir, créer si extension présente)

* SQL (après migration) :

```sql
CREATE EXTENSION IF NOT EXISTS vector;
-- example cosine ops name depends on pgvector version; adapt accordingly
CREATE INDEX IF NOT EXISTS idx_verse_embedding_hnsw ON bible_verse USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=200);
```

Documenter que cet index est créé conditionnellement (dev env may not have pgvector).

## 7. Services (fichiers)

* `bible/services/import_service.py` : orchestration import + resolve book mapping.
* `bible/services/cleaning.py` : `clean_text`, `normalize_book_name`, `strip_control_chars`.
* `bible/services/index_service.py` : populate tsv, create indexes (run SQL).
* `bible/services/embedding_service.py` : batch embeddings (uses OpenAI by default; pluggable adapter for SBERT).
* `bible/services/search_service.py` : `lexical_search(query, testament=None, limit=200)`, `hybrid_search(query, testament=None, top_k=50)`.
* `bible/services/aelf_service.py` : async httpx client to call AELF API.

## 8. Celery tasks & schedule

* `tasks.import_file_task(path, source_name)` — calls ImportService (synchronous work) and enqueues embedding jobs.
* `tasks.compute_embeddings_task(verse_ids)` — batch compute/update `Verse.embedding`.
* `tasks.populate_tsv_task(book_id)` — call IndexService.
* `tasks.fetch_aelf_daily()` — scheduled in Celery-beat daily at 02:00 UTC (configurable). It should:

  * call AELF endpoints for readings/messe/heures (use appropriate endpoints per AELF doc),
  * clean responses, store into `DailyText` (one record per reading),
  * link readings to verses if possible (use SearchService to shallow-match content and attach `book_id`, `chapter`, `verse` references in a JSON column if found),
  * retry on failure with exponential backoff, respect rate limits.

Env variables required:

* `DATABASE_URL`
* `REDIS_URL`
* `OPENAI_API_KEY` (optional)
* `AELF_API_BASE` (default `https://api.aelf.org`)
* `AELF_API_TOKEN` (if needed)
* `PGVECTOR_ENABLED` = true/false
* `EMBEDDING_PROVIDER` = `openai` | `sbert`
* Celery config (broker/backend)

## 9. API design (DRF) — endpoints & behavior

### Books & navigation (no heavy payloads)

* `GET /api/testaments/`

  * returns list `{slug, name, order}`
  * cache TTL 24h

* `GET /api/testaments/{slug}/books/`

  * returns books metadata in that testament: `{id, name, slug, order, verse_count}`
  * **no chapters nor verses** by default. Cache TTL 24h

* `GET /api/books/`

  * filter `?testament=ancien` optional

* `GET /api/books/{book_id}/`

  * `?expand=chapters` (if provided returns chapters metadata only; do **not** include verses).
  * include `url` fields for book and chapters

* `GET /api/books/{book_id}/chapters/`

  * `?page=` pagination, returns chapters list `{number, name, verse_count}`

* `GET /api/books/{book_id}/chapters/{number}/verses/`

  * paginated list of verses for the chapter: each verse `{number, text (or excerpt if ?excerpt=true), url}`
  * allow `?excerpt=true` to return substring (first 250 chars) to reduce payload for listing

* `GET /api/search/?q=...&testament=ancien&vector=true&group_by=book&page=1`

  * parameters:

    * `q` required
    * `vector` optional (true/false) — if true and `PGVECTOR_ENABLED` use hybrid search; else lexical only
    * `group_by=book` default — returns grouped results by book
    * `page` paginated across matches
  * Response structure (grouped by book):

```json
[
  {
    "book": {"id":12,"name":"Psaumes","slug":"psaumes","url":"/books/12/"},
    "matches": [
       {"chapter":1,"verse":2,"excerpt":"...","url":"/books/12/chapters/1/verses/2/"},
       ...
    ]
  }, ...
]
```

* `GET /api/verses/{verse_id}/` or `/books/{book_id}/chapters/{number}/verses/{verse_number}/`

  * return full verse object `{number, text, chapter, book}`

* `GET /api/daily_texts/`

  * list daily texts fetched from AELF (pagination + filters `?date=` `?category=`)

* `POST /api/import/` (authenticated admin)

  * multipart form: file upload + source_name; triggers Celery import task and returns task id

Security:

* Import endpoint and any write endpoints must be admin-only (token auth).
* Read endpoints public but rate-limited.

## 10. Search algorithm (hybrid) — implementation details

* Compute `q_embedding` using `EmbeddingService`.
* Vector step: `SELECT id, chapter_id, 1.0/(1 + (embedding <-> q_vec)) AS vscore FROM verse ORDER BY embedding <-> q_vec LIMIT 200`
* Lexical step: `SELECT id, chapter_id, ts_rank(tsv, plainto_tsquery('french', q)) AS tscore FROM verse WHERE tsv @@ plainto_tsquery('french', q) ORDER BY tscore DESC LIMIT 200`
* Union, normalize scores to [0,1], combine `combined = alpha * vscore + (1-alpha) * tscore` (default `alpha=0.7`), group by book and return top matches per book.
* If `PGVECTOR_ENABLED` is false, return lexical results only.
* If combined best score < `threshold_no_source` (e.g. 0.15), mark `no_internal_source=true` in response.

## 11. AELF integration (AELFService)

* Use `httpx.AsyncClient()` with configurable base URL (`AELF_API_BASE`).
* Endpoints to call (example patterns — consult AELF doc and use correct endpoints):

  * Daily readings, mass readings, hours endpoints — schedule calls and parse JSON response.
* Process:

  * fetch, clean text via `CleaningService`.
  * store in `DailyText` with `category` and `source_url`.
  * attempt to match content to verses via `SearchService.lexical_search` (fuzzy) and attach metadata `{book_id, chapter, verse_ids}` to `DailyText.local_matches` (JSONField).
* Rate limits: implement retries with exponential backoff (max 5 tries). Log all errors.

## 12. Caching strategy

* Use `django-redis` for caching responses.
* Cache keys:

  * `testaments_list` TTL 24h
  * `books_{testament}` TTL 24h
  * `book_{id}` TTL 1h (if expand false)
  * `search_{hash(q)+params}` TTL 2–30 min (shorter if vector=true)
  * `chapter_{book}_{num}` TTL 6h
* Invalidation: import tasks must invalidate relevant caches (books, book_{id}, search caches touching that book).

## 13. Logging & monitoring

* Log ingestion summary (books imported, verses created, errors).
* Record metrics:

  * ingestion_duration_seconds
  * verses_imported_count
  * indexing_duration_seconds
  * search_latency_ms
  * embedding_job_duration
  * aelf_fetch_success_count / failure_count
* Use standard Python logging; integrate Sentry optionally.

## 14. Security & performance notes

* Limit file import size; use streaming parse for huge files.
* Use transactions and chunked bulk_create to avoid long transactions.
* For public API, add rate limiting (simple DRF throttle).
* Ensure all DB queries use indexes; add explain if slow.

---

# Scripts & SQL fournis (à inclure dans le repo)

### SQL snippet (pgvector conditional)

```sql
-- create extension (if allowed)
CREATE EXTENSION IF NOT EXISTS vector;
-- create hnsw index if embedding column exists
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'bible_verse' ) AND
     EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='bible_verse' AND column_name='embedding') THEN
    EXECUTE 'CREATE INDEX IF NOT EXISTS idx_verse_embedding_hnsw ON bible_verse USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 200);';
  END IF;
END$$;
```

### SQL snippet (tsvector population)

```sql
UPDATE bible_verse SET tsv = to_tsvector('french', text) WHERE tsv IS NULL;
CREATE INDEX IF NOT EXISTS idx_verse_tsv ON bible_verse USING gin(tsv);
```

---