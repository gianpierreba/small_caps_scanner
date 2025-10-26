-- ============================================================================
-- Database Initialization Script
-- ============================================================================
-- Purpose: Create the main trading database and enable required extensions
-- Run this first as a PostgreSQL superuser
-- ============================================================================

-- Create database if it doesn't exist
-- Note: This must be run outside of a transaction block
-- You may need to run this manually: CREATE DATABASE trading;

-- Connect to the trading database before running the rest of the scripts
-- \c trading

-- Enable UUID extension for generating unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for text search performance (optional but recommended)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Set timezone to UTC for consistent timestamp handling
SET timezone = 'UTC';

-- Display success message
DO $$
BEGIN
    RAISE NOTICE 'Database initialization complete';
    RAISE NOTICE 'Extensions enabled: uuid-ossp, pg_trgm';
    RAISE NOTICE 'Timezone set to: UTC';
END $$;
