-- ============================================================================
-- After Market Schema Tables
-- ============================================================================
-- Purpose: Tables for storing after-market trading session scanner results
-- ============================================================================

SET search_path TO after_market, public;

-- ============================================================================
-- Table: after_market_scanner
-- Purpose: Stocks identified during after-market scanning sessions
-- ============================================================================
CREATE TABLE IF NOT EXISTS after_market_scanner (
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

COMMENT ON TABLE after_market_scanner IS 'Stocks identified in after-hours trading';
COMMENT ON COLUMN after_market_scanner.stock_uuid IS 'Foreign key reference to equities.stock_data';
COMMENT ON COLUMN after_market_scanner.quote_time IS 'Timestamp when stock was scanned in after-market';
COMMENT ON COLUMN after_market_scanner.float_rotation IS 'Percentage of float traded';

-- Display success message
DO $$
BEGIN
    RAISE NOTICE 'After market schema tables created successfully';
    RAISE NOTICE 'Tables: after_market_scanner';
END $$;
