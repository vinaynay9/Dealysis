-- Dealysis Database Schema
-- PostgreSQL Database Schema for Investment Memo Generator
-- 
-- This schema supports:
-- - User authentication (Auth.js)
-- - Investment memo storage and management
-- - Usage tracking and analytics
--
-- Database: PostgreSQL 14+
-- Recommended: Neon Serverless PostgreSQL

-- =============================================================================
-- AUTHENTICATION TABLES (Auth.js)
-- =============================================================================

-- Users table - stores user account information
CREATE TABLE IF NOT EXISTS auth_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255),
    email VARCHAR(255) UNIQUE NOT NULL,
    "emailVerified" TIMESTAMP WITH TIME ZONE,
    image TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_auth_users_email ON auth_users(email);

-- Accounts table - stores OAuth and credential provider information
CREATE TABLE IF NOT EXISTS auth_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "userId" UUID NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    provider VARCHAR(255) NOT NULL,
    type VARCHAR(255) NOT NULL,
    "providerAccountId" VARCHAR(255) NOT NULL,
    access_token TEXT,
    expires_at BIGINT,
    refresh_token TEXT,
    id_token TEXT,
    scope TEXT,
    session_state TEXT,
    token_type VARCHAR(255),
    password TEXT, -- Argon2 hashed password for credential provider
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE("providerAccountId", provider)
);

CREATE INDEX idx_auth_accounts_user_id ON auth_accounts("userId");
CREATE INDEX idx_auth_accounts_provider ON auth_accounts(provider, "providerAccountId");

-- Sessions table - stores active user sessions
CREATE TABLE IF NOT EXISTS auth_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "sessionToken" VARCHAR(255) UNIQUE NOT NULL,
    "userId" UUID NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    expires TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_auth_sessions_token ON auth_sessions("sessionToken");
CREATE INDEX idx_auth_sessions_user_id ON auth_sessions("userId");

-- Verification tokens table - for email verification and password reset
CREATE TABLE IF NOT EXISTS auth_verification_token (
    identifier VARCHAR(255) NOT NULL,
    token VARCHAR(255) NOT NULL,
    expires TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (identifier, token)
);

CREATE INDEX idx_auth_verification_token ON auth_verification_token(token);

-- =============================================================================
-- APPLICATION TABLES
-- =============================================================================

-- User memos table - stores generated and saved investment memos
CREATE TABLE IF NOT EXISTS user_memos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    company_name VARCHAR(255),
    content TEXT NOT NULL,
    sections JSONB, -- Structured section data with metadata
    metadata JSONB, -- Generation metadata (timestamp, file counts, etc.)
    is_favorite BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_user_memos_user_id ON user_memos(user_id);
CREATE INDEX idx_user_memos_company_name ON user_memos(company_name);
CREATE INDEX idx_user_memos_created_at ON user_memos(created_at DESC);
CREATE INDEX idx_user_memos_updated_at ON user_memos(updated_at DESC);
CREATE INDEX idx_user_memos_is_favorite ON user_memos(user_id, is_favorite) WHERE is_favorite = TRUE;

-- Full-text search index on memos
CREATE INDEX idx_user_memos_content_search ON user_memos USING gin(to_tsvector('english', content));
CREATE INDEX idx_user_memos_title_search ON user_memos USING gin(to_tsvector('english', title));

-- Usage tracking table - analytics and usage metrics
CREATE TABLE IF NOT EXISTS usage_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth_users(id) ON DELETE SET NULL,
    user_session_id VARCHAR(255), -- For anonymous tracking
    company_name VARCHAR(255),
    files_uploaded_count INTEGER DEFAULT 0,
    reference_texts_count INTEGER DEFAULT 0,
    reference_urls_count INTEGER DEFAULT 0,
    company_context TEXT,
    user_notes TEXT,
    processing_time_seconds INTEGER,
    sections_generated INTEGER DEFAULT 0,
    generation_successful BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_usage_tracking_user_id ON usage_tracking(user_id);
CREATE INDEX idx_usage_tracking_created_at ON usage_tracking(created_at DESC);
CREATE INDEX idx_usage_tracking_successful ON usage_tracking(generation_successful);

-- =============================================================================
-- FUNCTIONS & TRIGGERS
-- =============================================================================

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for user_memos updated_at
CREATE TRIGGER update_user_memos_updated_at
    BEFORE UPDATE ON user_memos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for auth_users updated_at
CREATE TRIGGER update_auth_users_updated_at
    BEFORE UPDATE ON auth_users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- SAMPLE QUERIES
-- =============================================================================

-- Get user with their memos count
-- SELECT 
--     u.id, 
--     u.email, 
--     u.name,
--     COUNT(m.id) as memo_count
-- FROM auth_users u
-- LEFT JOIN user_memos m ON u.id = m.user_id
-- GROUP BY u.id, u.email, u.name;

-- Search memos by content
-- SELECT id, title, company_name, created_at
-- FROM user_memos
-- WHERE user_id = 'user-uuid-here'
-- AND to_tsvector('english', content) @@ to_tsquery('english', 'artificial & intelligence');

-- Get usage statistics
-- SELECT 
--     DATE(created_at) as date,
--     COUNT(*) as total_attempts,
--     SUM(CASE WHEN generation_successful THEN 1 ELSE 0 END) as successful,
--     AVG(processing_time_seconds) as avg_processing_time,
--     AVG(files_uploaded_count) as avg_files_uploaded
-- FROM usage_tracking
-- WHERE created_at >= NOW() - INTERVAL '30 days'
-- GROUP BY DATE(created_at)
-- ORDER BY date DESC;

-- =============================================================================
-- CLEANUP & MAINTENANCE
-- =============================================================================

-- Delete expired sessions (run periodically)
-- DELETE FROM auth_sessions WHERE expires < NOW();

-- Delete expired verification tokens
-- DELETE FROM auth_verification_token WHERE expires < NOW();

-- =============================================================================
-- PERMISSIONS (Optional - for RLS or multi-tenant setup)
-- =============================================================================

-- Enable Row Level Security if needed
-- ALTER TABLE user_memos ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own memos
-- CREATE POLICY user_memos_user_isolation ON user_memos
--     FOR ALL
--     USING (user_id = current_setting('app.current_user_id')::UUID);

-- =============================================================================
-- NOTES
-- =============================================================================

-- 1. All tables use UUID for primary keys (more secure, better distribution)
-- 2. Timestamps are stored with timezone for accurate tracking
-- 3. Indexes are optimized for common query patterns
-- 4. Full-text search enabled on memos for fast content search
-- 5. Cascade deletes ensure data integrity when users are deleted
-- 6. The sections column in user_memos stores structured JSON:
--    {
--      "executive_summary": {
--        "title": "Executive Summary",
--        "content": "...",
--        "timestamp": "2024-01-01T00:00:00Z"
--      },
--      ...
--    }
-- 7. The metadata column stores generation metadata:
--    {
--      "generated": "2024-01-01T00:00:00Z",
--      "totalSections": 8,
--      "referenceMaterials": 5
--    }

