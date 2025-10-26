-- ============================================================================
-- Schema Creation Script
-- ============================================================================
-- Purpose: Create all database schemas for organizing tables
-- Run this after 00_init_database.sql
-- ============================================================================

-- Schema: equities
-- Purpose: Core stock data including company information, fundamentals,
--          short interest, news, and ticker history
CREATE SCHEMA IF NOT EXISTS equities;
COMMENT ON SCHEMA equities IS 'Core stock data, short interest, news, and ticker history';

-- Schema: pre_market
-- Purpose: Pre-market trading session scanner results
CREATE SCHEMA IF NOT EXISTS pre_market;
COMMENT ON SCHEMA pre_market IS 'Pre-market scanner results';

-- Schema: regular_market
-- Purpose: Regular market trading session scanner results
CREATE SCHEMA IF NOT EXISTS regular_market;
COMMENT ON SCHEMA regular_market IS 'Regular market scanner results';

-- Schema: after_market
-- Purpose: After-market trading session scanner results
CREATE SCHEMA IF NOT EXISTS after_market;
COMMENT ON SCHEMA after_market IS 'After-market scanner results';

-- Schema: schwab_access
-- Purpose: Charles Schwab API OAuth tokens and authentication data
CREATE SCHEMA IF NOT EXISTS schwab_access;
COMMENT ON SCHEMA schwab_access IS 'Schwab API access and refresh tokens';

-- Display success message
DO $$
BEGIN
    RAISE NOTICE 'All schemas created successfully';
    RAISE NOTICE 'Schemas: equities, pre_market, regular_market, after_market, schwab_access';
END $$;
