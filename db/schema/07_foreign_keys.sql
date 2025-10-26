-- ============================================================================
-- Foreign Key Constraints
-- ============================================================================
-- Purpose: Establish referential integrity between tables
-- Run this after all table creation scripts
-- ============================================================================

-- ============================================================================
-- Equities Schema Foreign Keys
-- ============================================================================

-- ticker_history references stock_data
ALTER TABLE equities.ticker_history
    DROP CONSTRAINT IF EXISTS fk_ticker_history_stock_uuid;

ALTER TABLE equities.ticker_history
    ADD CONSTRAINT fk_ticker_history_stock_uuid
    FOREIGN KEY (stock_uuid)
    REFERENCES equities.stock_data(stock_uuid)
    ON DELETE CASCADE
    ON UPDATE CASCADE;

-- stock_short_data references stock_data
ALTER TABLE equities.stock_short_data
    DROP CONSTRAINT IF EXISTS fk_stock_short_data_stock_uuid;

ALTER TABLE equities.stock_short_data
    ADD CONSTRAINT fk_stock_short_data_stock_uuid
    FOREIGN KEY (stock_uuid)
    REFERENCES equities.stock_data(stock_uuid)
    ON DELETE CASCADE
    ON UPDATE CASCADE;

-- stock_news references stock_data
ALTER TABLE equities.stock_news
    DROP CONSTRAINT IF EXISTS fk_stock_news_stock_uuid;

ALTER TABLE equities.stock_news
    ADD CONSTRAINT fk_stock_news_stock_uuid
    FOREIGN KEY (stock_uuid)
    REFERENCES equities.stock_data(stock_uuid)
    ON DELETE CASCADE
    ON UPDATE CASCADE;

-- ============================================================================
-- Scanner Schema Foreign Keys
-- ============================================================================

-- pre_market_scanner references stock_data
ALTER TABLE pre_market.pre_market_scanner
    DROP CONSTRAINT IF EXISTS fk_pre_market_scanner_stock_uuid;

ALTER TABLE pre_market.pre_market_scanner
    ADD CONSTRAINT fk_pre_market_scanner_stock_uuid
    FOREIGN KEY (stock_uuid)
    REFERENCES equities.stock_data(stock_uuid)
    ON DELETE CASCADE
    ON UPDATE CASCADE;

-- regular_market_scanner references stock_data
ALTER TABLE regular_market.regular_market_scanner
    DROP CONSTRAINT IF EXISTS fk_regular_market_scanner_stock_uuid;

ALTER TABLE regular_market.regular_market_scanner
    ADD CONSTRAINT fk_regular_market_scanner_stock_uuid
    FOREIGN KEY (stock_uuid)
    REFERENCES equities.stock_data(stock_uuid)
    ON DELETE CASCADE
    ON UPDATE CASCADE;

-- after_market_scanner references stock_data
ALTER TABLE after_market.after_market_scanner
    DROP CONSTRAINT IF EXISTS fk_after_market_scanner_stock_uuid;

ALTER TABLE after_market.after_market_scanner
    ADD CONSTRAINT fk_after_market_scanner_stock_uuid
    FOREIGN KEY (stock_uuid)
    REFERENCES equities.stock_data(stock_uuid)
    ON DELETE CASCADE
    ON UPDATE CASCADE;

-- Display success message
DO $$
BEGIN
    RAISE NOTICE 'All foreign key constraints created successfully';
    RAISE NOTICE 'Referential integrity established between all tables';
END $$;
