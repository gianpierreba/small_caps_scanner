-- ============================================================================
-- Regular Market Schema Tables
-- ============================================================================
-- Purpose: Tables for storing regular market trading session scanner results
-- ============================================================================

SET search_path TO regular_market, public;

-- ============================================================================
-- Table: regular_market_scanner
-- Purpose: Stocks identified during regular market scanning sessions
-- ============================================================================
CREATE TABLE IF NOT EXISTS regular_market_scanner (
    stock_uuid UUID NOT NULL,

    -- Quote data with timezone-aware timestamp
    quote_time TIMESTAMP WITH TIME ZONE,

    -- Stock identifiers
    ticker CHARACTER VARYING(10) NOT NULL,

    -- Price and volume metrics
    last_price DOUBLE PRECISION,
    chg_percentage DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    stock_float DOUBLE PRECISION,

    -- Volume ratios
    float_rotation DOUBLE PRECISION,
    rel_vol_one_day DOUBLE PRECISION,
    rel_vol_ten_days DOUBLE PRECISION,
    rel_vol_three_months DOUBLE PRECISION
);

COMMENT ON TABLE regular_market_scanner IS 'Stocks identified during regular market hours';
COMMENT ON COLUMN regular_market_scanner.stock_uuid IS 'Foreign key reference to equities.stock_data';
COMMENT ON COLUMN regular_market_scanner.quote_time IS 'Timestamp when stock was scanned in regular market';
COMMENT ON COLUMN regular_market_scanner.float_rotation IS 'Percentage of float traded';

-- Display success message
DO $$
BEGIN
    RAISE NOTICE 'Regular market schema tables created successfully';
    RAISE NOTICE 'Tables: regular_market_scanner';
END $$;
