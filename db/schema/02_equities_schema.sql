-- ============================================================================
-- Equities Schema Tables
-- ============================================================================
-- Purpose: Core stock data tables including company information, fundamentals,
--          short interest, news articles, and ticker history
-- ============================================================================

SET search_path TO equities, public;

-- ============================================================================
-- Table: stock_data
-- Purpose: Main table storing comprehensive stock information and fundamentals
-- ============================================================================
CREATE TABLE IF NOT EXISTS stock_data (
    stock_uuid UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stock_uuId UUID UNIQUE NOT NULL DEFAULT uuid_generate_v4(),

    -- Quote data with timezone-aware timestamps
    quote_time TIMESTAMP WITH TIME ZONE,

    -- Stock identifiers
    ticker CHARACTER VARYING(10) NOT NULL UNIQUE,
    clk_number CHARACTER VARYING(20),
    company_name CHARACTER VARYING(200),

    -- Price and volume metrics
    stock_last DOUBLE PRECISION,
    chg_percentage DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    stock_float DOUBLE PRECISION,

    -- Volume averages
    float_rotation DOUBLE PRECISION,
    rel_vol_one_day DOUBLE PRECISION,
    rel_vol_ten_days DOUBLE PRECISION,
    rel_vol_three_months DOUBLE PRECISION,

    -- Financial metrics
    avg_one_day_volume DOUBLE PRECISION,
    avg_vol_ten_days DOUBLE PRECISION,
    operating_cash_flow DOUBLE PRECISION,

    -- Company details
    sector CHARACTER VARYING(200),
    industry CHARACTER VARYING(200),
    website CHARACTER VARYING(150),
    country CHARACTER VARYING(150),
    business_summary TEXT,

    -- Market cap
    market_cap DOUBLE PRECISION,

    -- Ownership percentages
    held_insiders DOUBLE PRECISION,
    held_institutions DOUBLE PRECISION
);

COMMENT ON TABLE stock_data IS 'Main table with company information, fundamentals, and market data';
COMMENT ON COLUMN stock_data.stock_uuid IS 'Primary key UUID';
COMMENT ON COLUMN stock_data.stock_uuId IS 'Alternative UUID identifier (note capitalization)';
COMMENT ON COLUMN stock_data.quote_time IS 'Timestamp of last quote update (timezone-aware)';
COMMENT ON COLUMN stock_data.ticker IS 'Stock ticker symbol (unique)';
COMMENT ON COLUMN stock_data.float_rotation IS 'Float rotation percentage';
COMMENT ON COLUMN stock_data.rel_vol_one_day IS 'Relative volume compared to 1-day average';
COMMENT ON COLUMN stock_data.rel_vol_ten_days IS 'Relative volume compared to 10-day average';
COMMENT ON COLUMN stock_data.rel_vol_three_months IS 'Relative volume compared to 3-month average';

-- ============================================================================
-- Table: stock_short_data
-- Purpose: Short interest metrics and tracking dates
-- ============================================================================
CREATE TABLE IF NOT EXISTS stock_short_data (
    stock_uuid UUID NOT NULL,
    ticker CHARACTER VARYING(10) NOT NULL,

    -- Short interest metrics
    shares_short DOUBLE PRECISION,
    short_ratio DOUBLE PRECISION,
    short_percent_float DOUBLE PRECISION,
    shares_percent_shares_outstanding DOUBLE PRECISION,
    shares_short_prior_month DOUBLE PRECISION,

    -- Short interest dates
    short_ratio_date TIMESTAMP WITHOUT TIME ZONE,
    shares_short_previous_month_date TIMESTAMP WITHOUT TIME ZONE
);

COMMENT ON TABLE stock_short_data IS 'Short interest metrics and dates';
COMMENT ON COLUMN stock_short_data.short_ratio IS 'Days to cover short positions';
COMMENT ON COLUMN stock_short_data.short_percent_float IS 'Percentage of float that is shorted';
COMMENT ON COLUMN stock_short_data.shares_percent_shares_outstanding IS 'Percentage of shares outstanding that are shorted';

-- ============================================================================
-- Table: stock_news
-- Purpose: Company news articles with deduplication via uuid_news
-- ============================================================================
CREATE TABLE IF NOT EXISTS stock_news (
    stock_uuid UUID NOT NULL,
    ticker CHARACTER VARYING(10) NOT NULL,
    uuid_news UUID NOT NULL,

    -- News article details
    title TEXT,
    publisher CHARACTER VARYING(100),
    link CHARACTER VARYING(350),
    publish_time TIMESTAMP WITH TIME ZONE,
    type CHARACTER VARYING(50),
    related_tickers CHARACTER VARYING(10)
);

COMMENT ON TABLE stock_news IS 'Company news articles with deduplication';
COMMENT ON COLUMN stock_news.uuid_news IS 'Unique identifier for news article (prevents duplicates)';
COMMENT ON COLUMN stock_news.related_tickers IS 'Related stock tickers mentioned in the article';

-- ============================================================================
-- Table: ticker_history
-- Purpose: Daily tracking of when tickers were scanned
-- ============================================================================
CREATE TABLE IF NOT EXISTS ticker_history (
    ticker_history_uuid UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stock_uuid UUID NOT NULL,

    -- Tracking information
    date DATE NOT NULL,
    week INTEGER
);

COMMENT ON TABLE ticker_history IS 'Daily tracking of when tickers were scanned';
COMMENT ON COLUMN ticker_history.date IS 'Date when the ticker was scanned';
COMMENT ON COLUMN ticker_history.week IS 'Week number of the year';

-- Display success message
DO $$
BEGIN
    RAISE NOTICE 'Equities schema tables created successfully';
    RAISE NOTICE 'Tables: stock_data, stock_short_data, stock_news, ticker_history';
END $$;
