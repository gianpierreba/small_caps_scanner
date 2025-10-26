-- ============================================================================
-- Performance Indexes
-- ============================================================================
-- Purpose: Create indexes to optimize query performance
-- Run this after all table and foreign key creation
-- ============================================================================

-- ============================================================================
-- Equities Schema Indexes
-- ============================================================================

-- Primary lookup: ticker symbol (most common query pattern)
CREATE INDEX IF NOT EXISTS idx_stock_data_ticker
    ON equities.stock_data(ticker);

-- Timestamp queries for recent data
CREATE INDEX IF NOT EXISTS idx_stock_data_quote_time
    ON equities.stock_data(quote_time DESC);

-- Company categorization queries
CREATE INDEX IF NOT EXISTS idx_stock_data_sector
    ON equities.stock_data(sector);

CREATE INDEX IF NOT EXISTS idx_stock_data_industry
    ON equities.stock_data(industry);

-- Market cap queries (filtering by size)
CREATE INDEX IF NOT EXISTS idx_stock_data_market_cap
    ON equities.stock_data(market_cap);

-- ticker_history indexes for historical queries
CREATE INDEX IF NOT EXISTS idx_ticker_history_stock_uuid
    ON equities.ticker_history(stock_uuid);

CREATE INDEX IF NOT EXISTS idx_ticker_history_date
    ON equities.ticker_history(date DESC);

CREATE INDEX IF NOT EXISTS idx_ticker_history_week
    ON equities.ticker_history(week);

-- Composite index for date-based stock lookups
CREATE INDEX IF NOT EXISTS idx_ticker_history_stock_date
    ON equities.ticker_history(stock_uuid, date DESC);

-- stock_short_data indexes
CREATE INDEX IF NOT EXISTS idx_stock_short_data_stock_uuid
    ON equities.stock_short_data(stock_uuid);

CREATE INDEX IF NOT EXISTS idx_stock_short_data_ticker
    ON equities.stock_short_data(ticker);

-- Short interest percentage for high short interest queries
CREATE INDEX IF NOT EXISTS idx_stock_short_data_short_percent
    ON equities.stock_short_data(short_percent_float DESC);

-- stock_news indexes
CREATE INDEX IF NOT EXISTS idx_stock_news_stock_uuid
    ON equities.stock_news(stock_uuid);

CREATE INDEX IF NOT EXISTS idx_stock_news_ticker
    ON equities.stock_news(ticker);

CREATE INDEX IF NOT EXISTS idx_stock_news_uuid_news
    ON equities.stock_news(uuid_news);

CREATE INDEX IF NOT EXISTS idx_stock_news_publish_time
    ON equities.stock_news(publish_time DESC);

-- Composite index for recent news by stock
CREATE INDEX IF NOT EXISTS idx_stock_news_stock_time
    ON equities.stock_news(stock_uuid, publish_time DESC);

-- ============================================================================
-- Pre-Market Scanner Indexes
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_pre_market_scanner_stock_uuid
    ON pre_market.pre_market_scanner(stock_uuid);

CREATE INDEX IF NOT EXISTS idx_pre_market_scanner_ticker
    ON pre_market.pre_market_scanner(ticker);

CREATE INDEX IF NOT EXISTS idx_pre_market_scanner_quote_time
    ON pre_market.pre_market_scanner(quote_time DESC);

-- Performance metrics for top movers
CREATE INDEX IF NOT EXISTS idx_pre_market_scanner_chg_percentage
    ON pre_market.pre_market_scanner(chg_percentage DESC);

CREATE INDEX IF NOT EXISTS idx_pre_market_scanner_volume
    ON pre_market.pre_market_scanner(volume DESC);

CREATE INDEX IF NOT EXISTS idx_pre_market_scanner_float_rotation
    ON pre_market.pre_market_scanner(float_rotation DESC);

-- ============================================================================
-- Regular Market Scanner Indexes
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_regular_market_scanner_stock_uuid
    ON regular_market.regular_market_scanner(stock_uuid);

CREATE INDEX IF NOT EXISTS idx_regular_market_scanner_ticker
    ON regular_market.regular_market_scanner(ticker);

CREATE INDEX IF NOT EXISTS idx_regular_market_scanner_quote_time
    ON regular_market.regular_market_scanner(quote_time DESC);

-- Performance metrics for top movers
CREATE INDEX IF NOT EXISTS idx_regular_market_scanner_chg_percentage
    ON regular_market.regular_market_scanner(chg_percentage DESC);

CREATE INDEX IF NOT EXISTS idx_regular_market_scanner_volume
    ON regular_market.regular_market_scanner(volume DESC);

CREATE INDEX IF NOT EXISTS idx_regular_market_scanner_float_rotation
    ON regular_market.regular_market_scanner(float_rotation DESC);

-- ============================================================================
-- After Market Scanner Indexes
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_after_market_scanner_stock_uuid
    ON after_market.after_market_scanner(stock_uuid);

CREATE INDEX IF NOT EXISTS idx_after_market_scanner_ticker
    ON after_market.after_market_scanner(ticker);

CREATE INDEX IF NOT EXISTS idx_after_market_scanner_quote_time
    ON after_market.after_market_scanner(quote_time DESC);

-- Performance metrics for top movers
CREATE INDEX IF NOT EXISTS idx_after_market_scanner_chg_percentage
    ON after_market.after_market_scanner(chg_percentage DESC);

CREATE INDEX IF NOT EXISTS idx_after_market_scanner_volume
    ON after_market.after_market_scanner(volume DESC);

CREATE INDEX IF NOT EXISTS idx_after_market_scanner_float_rotation
    ON after_market.after_market_scanner(float_rotation DESC);

-- ============================================================================
-- Schwab Access Schema Indexes
-- ============================================================================

-- Time-based lookups for token expiration checks
CREATE INDEX IF NOT EXISTS idx_schwab_access_time
    ON schwab_access.schwab_access_refresh_token(time DESC);

-- Display success message
DO $$
BEGIN
    RAISE NOTICE 'All performance indexes created successfully';
    RAISE NOTICE 'Database is now optimized for common query patterns';
END $$;
