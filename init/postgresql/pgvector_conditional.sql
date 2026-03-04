BEGIN;

-- create extension (if allowed)
-- We use a DO block to catch if extension vector is not physically available in this pg image
DO $$
BEGIN
    EXECUTE 'CREATE EXTENSION IF NOT EXISTS vector;';
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'pgvector extension could not be created : %', SQLERRM;
END$$;

-- create hnsw index if embedding column exists and vector is installed
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        IF EXISTS (SELECT 1 FROM pg_class WHERE relname = 'bible_verse' ) AND
           EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='bible_verse' AND column_name='embedding') THEN
           EXECUTE 'CREATE INDEX IF NOT EXISTS idx_verse_embedding_hnsw ON bible_verse USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 200);';
        END IF;
    END IF;
END$$;

UPDATE bible_verse SET tsv = to_tsvector('french', text) WHERE tsv IS NULL;
CREATE INDEX IF NOT EXISTS idx_verse_tsv ON bible_verse USING gin(tsv);

COMMIT;