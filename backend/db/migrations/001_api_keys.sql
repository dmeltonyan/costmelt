-- Migration: Create api_keys table for Cost Melt authentication
-- Created: 2025-01-XX
-- Description: Stores API keys with bcrypt hashing, role-based access, and usage tracking

-- Create api_keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    key_hash TEXT NOT NULL,  -- bcrypt hash of the full API key
    prefix TEXT NOT NULL,    -- First 8 characters for fast lookup
    role TEXT NOT NULL CHECK (role IN ('admin', 'write', 'read')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,  -- NULL means never expires
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'revoked')),
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Constraints
    CONSTRAINT valid_prefix_length CHECK (LENGTH(prefix) = 8),
    CONSTRAINT valid_key_hash CHECK (LENGTH(key_hash) > 0)
);

-- Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON api_keys(prefix);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_project ON api_keys(user_id, project_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_status ON api_keys(status) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_api_keys_expires_at ON api_keys(expires_at) WHERE expires_at IS NOT NULL;

-- Create function to update last_used_at
CREATE OR REPLACE FUNCTION update_api_key_last_used()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE api_keys
    SET last_used_at = NOW()
    WHERE id = NEW.id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update last_used_at (optional, can be done in application)
-- Note: We'll update this in the application code instead for better control

-- Add comments for documentation
COMMENT ON TABLE api_keys IS 'Stores API keys with bcrypt hashing for Cost Melt authentication';
COMMENT ON COLUMN api_keys.key_hash IS 'bcrypt hash of the full API key (never store plaintext)';
COMMENT ON COLUMN api_keys.prefix IS 'First 8 characters of the key for fast database lookup';
COMMENT ON COLUMN api_keys.role IS 'Access role: admin (full access), write (can call /v1/route), read (metrics only)';
COMMENT ON COLUMN api_keys.status IS 'Key status: active (usable) or revoked (disabled)';
COMMENT ON COLUMN api_keys.expires_at IS 'Optional expiration timestamp. NULL means never expires';

