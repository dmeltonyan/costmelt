-- Cost Melt Database Schema
-- Supabase PostgreSQL Schema with pgvector extension

-- Enable pgvector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Requests table - logs all LLM requests
CREATE TABLE IF NOT EXISTS requests (
    id SERIAL PRIMARY KEY,
    prompt TEXT NOT NULL,
    response TEXT NOT NULL,
    model_used VARCHAR(50) NOT NULL,
    tokens_used INTEGER NOT NULL,
    cost FLOAT NOT NULL,
    cache_hit BOOLEAN DEFAULT FALSE,
    compressed BOOLEAN DEFAULT FALSE,
    user_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create index on user_id for faster queries
CREATE INDEX IF NOT EXISTS idx_requests_user_id ON requests(user_id);
CREATE INDEX IF NOT EXISTS idx_requests_created_at ON requests(created_at);
CREATE INDEX IF NOT EXISTS idx_requests_model_used ON requests(model_used);

-- Cache table - stores cached prompt-response pairs with embeddings
CREATE TABLE IF NOT EXISTS cache (
    id SERIAL PRIMARY KEY,
    prompt TEXT NOT NULL,
    response TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI text-embedding-3-small dimension
    model_used VARCHAR(50) NOT NULL,
    tokens_used INTEGER NOT NULL,
    cost FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    last_accessed TIMESTAMP DEFAULT NOW()
);

-- Create index on embedding for vector similarity search
CREATE INDEX IF NOT EXISTS idx_cache_embedding ON cache 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Users table - extends Supabase Auth
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) PRIMARY KEY,  -- Supabase Auth UUID
    email VARCHAR(255) UNIQUE NOT NULL,
    plan VARCHAR(50) DEFAULT 'free',
    api_key VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- API Keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_api_keys_key ON api_keys(key);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);

-- Function for vector similarity search
CREATE OR REPLACE FUNCTION search_similar_cache(
    query_embedding vector(1536),
    similarity_threshold FLOAT DEFAULT 0.92,
    match_limit INTEGER DEFAULT 1
)
RETURNS TABLE (
    id INTEGER,
    prompt TEXT,
    response TEXT,
    model_used VARCHAR(50),
    tokens_used INTEGER,
    cost FLOAT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.prompt,
        c.response,
        c.model_used,
        c.tokens_used,
        c.cost,
        1 - (c.embedding <=> query_embedding) AS similarity
    FROM cache c
    WHERE 1 - (c.embedding <=> query_embedding) > similarity_threshold
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_limit;
END;
$$;

-- Update last_accessed timestamp on cache hit
CREATE OR REPLACE FUNCTION update_cache_access()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE cache SET last_accessed = NOW() WHERE id = NEW.id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update last_accessed (would be called from application)
-- Note: This is a placeholder - actual implementation depends on usage pattern

