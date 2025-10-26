-- ============================================================================
-- Schwab Access Schema Tables
-- ============================================================================
-- Purpose: Charles Schwab API OAuth tokens and authentication data
-- ============================================================================

SET search_path TO schwab_access, public;

-- ============================================================================
-- Table: schwab_access_refresh_token
-- Purpose: Store OAuth access and refresh tokens for Schwab API authentication
-- ============================================================================
CREATE TABLE IF NOT EXISTS schwab_access_refresh_token (
    access_refresh_token_uuid UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Token timestamp
    time TIMESTAMP WITHOUT TIME ZONE NOT NULL,

    -- Token expiration
    expires_in INTEGER NOT NULL,

    -- Token type and scope
    token_type CHARACTER VARYING(10) NOT NULL,
    scope CHARACTER VARYING(500),

    -- OAuth tokens
    refresh_token CHARACTER VARYING(500) NOT NULL,
    access_token CHARACTER VARYING(500) NOT NULL,
    id_token CHARACTER VARYING(500)
);

COMMENT ON TABLE schwab_access_refresh_token IS 'OAuth tokens for Schwab API authentication';
COMMENT ON COLUMN schwab_access_refresh_token.access_refresh_token_uuid IS 'Primary key UUID';
COMMENT ON COLUMN schwab_access_refresh_token.time IS 'Timestamp when token was created';
COMMENT ON COLUMN schwab_access_refresh_token.expires_in IS 'Token expiration time in seconds (typically 1800 = 30 minutes)';
COMMENT ON COLUMN schwab_access_refresh_token.token_type IS 'OAuth token type (typically "Bearer")';
COMMENT ON COLUMN schwab_access_refresh_token.scope IS 'OAuth scope permissions granted';
COMMENT ON COLUMN schwab_access_refresh_token.refresh_token IS 'Refresh token (valid for 7 days)';
COMMENT ON COLUMN schwab_access_refresh_token.access_token IS 'Access token (valid for 30 minutes)';
COMMENT ON COLUMN schwab_access_refresh_token.id_token IS 'OpenID Connect ID token';

-- Display success message
DO $$
BEGIN
    RAISE NOTICE 'Schwab access schema tables created successfully';
    RAISE NOTICE 'Tables: schwab_access_refresh_token';
END $$;
