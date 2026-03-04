-- Script to create necessary indexes (GIN for text, HNSW for vector)

-- 1. Full-text search (tsvector) on verse text
-- A built-in GIN index on bible_verse(tsv) is already created via Django's Python migration,
-- but we define it here as a fallback or for custom setups.
CREATE INDEX IF NOT EXISTS idx_verse_tsv 
ON bible_verse USING GIN (tsv);

-- 2. Trigram indexing (optional, for partial matching if required)
-- CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- CREATE INDEX IF NOT EXISTS idx_verse_text_trgm 
-- ON bible_verse USING GIN (text gin_trgm_ops);

-- 3. pgvector HNSW index
-- This is applied ONLY if pgvector is enabled in the environment.
-- The python code does not execute this directly unless the extension is active.
-- CREATE EXTENSION IF NOT EXISTS vector;
-- CREATE INDEX IF NOT EXISTS idx_verse_embedding_hnsw 
-- ON bible_verse USING hnsw (embedding vector_cosine_ops)
-- WITH (m = 16, ef_construction = 64);
