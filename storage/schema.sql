CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS files (
    file_id UUID PRIMARY KEY,
    repo_id TEXT NOT NULL,
    path TEXT NOT NULL,
    language TEXT,
    file_type TEXT,
    loc INT,
    content_hash TEXT,
    UNIQUE (repo_id, path)
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id UUID PRIMARY KEY,
    file_id UUID NOT NULL
        REFERENCES files(file_id)
        ON DELETE CASCADE,
    symbol_id TEXT NOT NULL UNIQUE,
    start_line INT NOT NULL,
    end_line INT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(384)
);

CREATE INDEX IF NOT EXISTS chunks_embedding_idx
ON chunks
USING ivfflat (embedding vector_cosine_ops);