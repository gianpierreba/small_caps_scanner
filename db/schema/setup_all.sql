-- ============================================================================
-- Master Database Setup Script
-- ============================================================================
-- Purpose: Execute all schema creation scripts in the correct order
--
-- Usage:
--   1. First create the database manually:
--      CREATE DATABASE trading;
--
--   2. Then connect to it and run this script:
--      psql -U your_username -d trading -f setup_all.sql
--
-- Or run individual scripts in order:
--   psql -U your_username -d trading -f 00_init_database.sql
--   psql -U your_username -d trading -f 01_create_schemas.sql
--   ... etc
-- ============================================================================

\echo '================================================================================'
\echo 'Starting Stock Market Scanner Database Setup'
\echo '================================================================================'
\echo ''

-- Ensure we're connected to the trading database
SELECT current_database();

\echo ''
\echo '================================================================================'
\echo 'Step 1/9: Initializing database and extensions...'
\echo '================================================================================'
\i 00_init_database.sql

\echo ''
\echo '================================================================================'
\echo 'Step 2/9: Creating schemas...'
\echo '================================================================================'
\i 01_create_schemas.sql

\echo ''
\echo '================================================================================'
\echo 'Step 3/9: Creating equities schema tables...'
\echo '================================================================================'
\i 02_equities_schema.sql

\echo ''
\echo '================================================================================'
\echo 'Step 4/9: Creating pre_market schema tables...'
\echo '================================================================================'
\i 03_pre_market_schema.sql

\echo ''
\echo '================================================================================'
\echo 'Step 5/9: Creating regular_market schema tables...'
\echo '================================================================================'
\i 04_regular_market_schema.sql

\echo ''
\echo '================================================================================'
\echo 'Step 6/9: Creating after_market schema tables...'
\echo '================================================================================'
\i 05_after_market_schema.sql

\echo ''
\echo '================================================================================'
\echo 'Step 7/9: Creating schwab_access schema tables...'
\echo '================================================================================'
\i 06_schwab_access_schema.sql

\echo ''
\echo '================================================================================'
\echo 'Step 8/9: Creating foreign key constraints...'
\echo '================================================================================'
\i 07_foreign_keys.sql

\echo ''
\echo '================================================================================'
\echo 'Step 9/9: Creating performance indexes...'
\echo '================================================================================'
\i 08_indexes.sql

\echo ''
\echo '================================================================================'
\echo 'Database Setup Complete!'
\echo '================================================================================'
\echo ''
\echo 'Summary:'
\echo '  - Database: trading'
\echo '  - Schemas: 5 (equities, pre_market, regular_market, after_market, schwab_access)'
\echo '  - Tables: 8'
\echo '  - Foreign Keys: 6'
\echo '  - Indexes: 40+'
\echo ''
\echo 'Next Steps:'
\echo '  1. Configure your database connection in the application'
\echo '  2. Set up environment variables for Schwab API credentials'
\echo '  3. Run the scanner: python main.py'
\echo ''
\echo 'For detailed instructions, see: db/schema/README.md'
\echo '================================================================================'
