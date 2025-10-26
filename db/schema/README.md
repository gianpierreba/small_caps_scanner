# Database Schema Setup

This directory contains SQL scripts to create the complete database schema for the Stock Market Scanner application.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
  - [Option 1: SQL Master Script (Recommended)](#option-1-sql-master-script-recommended---stable-)
  - [Option 2: Automated Scripts (Under Development)](#option-2-automated-scripts-under-development---not-yet-available-)
  - [Option 3: Individual SQL Scripts](#option-3-individual-sql-scripts)
- [Script Descriptions](#script-descriptions)
- [Database Schema Details](#database-schema-details)
  - [Equities Schema](#equities-schema)
  - [Scanner Schemas](#scanner-schemas)
  - [Schwab Access Schema](#schwab-access-schema)
- [Foreign Key Relationships](#foreign-key-relationships)
- [Performance Indexes](#performance-indexes)
- [Verification](#verification)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Backup and Restore](#backup-and-restore)
- [Next Steps](#next-steps)
- [Support](#support)

---

## Overview

The database consists of **5 schemas** containing **8 tables** with comprehensive foreign key relationships and performance indexes:

| Schema | Tables | Purpose |
|--------|--------|---------|
| `equities` | stock_data, stock_short_data, stock_news, ticker_history | Core stock data and metadata |
| `pre_market` | pre_market_scanner | Pre-market session results |
| `regular_market` | regular_market_scanner | Regular trading hours results |
| `after_market` | after_market_scanner | After-hours trading results |
| `schwab_access` | schwab_access_refresh_token | Schwab API OAuth tokens |

## Prerequisites

- PostgreSQL 12+ installed and running
- PostgreSQL client tools (`psql`)
- Superuser access to create databases (or use an existing database)

## Quick Start

### Option 1: SQL Master Script (Recommended - Stable) ✅

**Works on: Any platform with psql**

```bash
# Step 1: Create the database
psql -U postgres -c "CREATE DATABASE trading;"

# Step 2: Run the master setup script
cd db/schema
psql -U postgres -d trading -f setup_all.sql
```

This is the **most reliable method** and works universally.

---

### Option 2: Automated Scripts (Under Development - Not Yet Available) ⚠️

> **⚠️ Note**: The following automated scripts (`setup.py` and `setup.sh`) are currently under development and testing.
> They are **not included in the current release** and will be published in a future version.
>
> **For now, please use Option 1 (setup_all.sql) for database setup.**

<details>
<summary><strong>Preview: Python Script (Coming Soon)</strong></summary>

```bash
cd db/schema
python setup.py
```

Features (when released):
- ✅ Cross-platform (Windows, macOS, Linux)
- ✅ Better error handling
- ✅ Password prompt for security
</details>

<details>
<summary><strong>Preview: Bash Script (Coming Soon)</strong></summary>

```bash
cd db/schema
./setup.sh
```

Features (when released):
- ✅ Unix/Linux/macOS native
- ✅ Git Bash on Windows, WSL support
</details>

---

### Option 3: Individual SQL Scripts

1. Create the database:
```bash
psql -U postgres -c "CREATE DATABASE trading;"
```

2. Run the master setup script:
```bash
cd db/schema
psql -U postgres -d trading -f setup_all.sql
```

### Option 3: Individual Scripts

Run each script in order:

```bash
psql -U postgres -d trading -f 00_init_database.sql
psql -U postgres -d trading -f 01_create_schemas.sql
psql -U postgres -d trading -f 02_equities_schema.sql
psql -U postgres -d trading -f 03_pre_market_schema.sql
psql -U postgres -d trading -f 04_regular_market_schema.sql
psql -U postgres -d trading -f 05_after_market_schema.sql
psql -U postgres -d trading -f 06_schwab_access_schema.sql
psql -U postgres -d trading -f 07_foreign_keys.sql
psql -U postgres -d trading -f 08_indexes.sql
```

## Script Descriptions

| Script | Purpose |
|--------|---------|
| `00_init_database.sql` | Enable PostgreSQL extensions (uuid-ossp, pg_trgm) |
| `01_create_schemas.sql` | Create all 5 database schemas |
| `02_equities_schema.sql` | Create core stock data tables |
| `03_pre_market_schema.sql` | Create pre-market scanner table |
| `04_regular_market_schema.sql` | Create regular market scanner table |
| `05_after_market_schema.sql` | Create after-market scanner table |
| `06_schwab_access_schema.sql` | Create Schwab API token storage table |
| `07_foreign_keys.sql` | Establish foreign key constraints |
| `08_indexes.sql` | Create performance indexes |
| `setup_all.sql` | **Master script that runs all scripts in order** ⭐ |
| `setup.py` | Python automation script *(under development, not yet published)* |
| `setup.sh` | Bash automation script *(under development, not yet published)* |

## Database Schema Details

### Equities Schema

**stock_data** - Main table with company information and fundamentals
- Primary Key: `stock_uuid` (UUID)
- Unique: `ticker` (VARCHAR 10)
- Contains: quote data, fundamentals, ownership, company details

**stock_short_data** - Short interest metrics
- References: `stock_data.stock_uuid`
- Contains: short ratio, short float %, shares short

**stock_news** - Company news articles
- References: `stock_data.stock_uuid`
- Unique: `uuid_news` (prevents duplicate news)
- Contains: title, publisher, link, timestamp

**ticker_history** - Daily ticker scan tracking
- References: `stock_data.stock_uuid`
- Contains: scan date, week number

### Scanner Schemas

All scanner tables share the same structure:

**pre_market_scanner** / **regular_market_scanner** / **after_market_scanner**
- References: `equities.stock_data.stock_uuid`
- Contains: ticker, quote data, volume metrics, float rotation

### Schwab Access Schema

**schwab_access_refresh_token** - OAuth token storage
- Primary Key: `access_refresh_token_uuid`
- Contains: access tokens, refresh tokens, expiration times

## Foreign Key Relationships

All scanner tables and equities child tables reference `equities.stock_data` via `stock_uuid`:

```
equities.stock_data (stock_uuid)
    ├── equities.ticker_history (stock_uuid)
    ├── equities.stock_short_data (stock_uuid)
    ├── equities.stock_news (stock_uuid)
    ├── pre_market.pre_market_scanner (stock_uuid)
    ├── regular_market.regular_market_scanner (stock_uuid)
    └── after_market.after_market_scanner (stock_uuid)
```

Cascade rules: `ON DELETE CASCADE ON UPDATE CASCADE`

## Performance Indexes

40+ indexes created for optimal query performance:

### Primary Indexes
- Ticker lookups: `idx_stock_data_ticker`
- Time-based queries: `idx_*_quote_time`
- UUID lookups: All `stock_uuid` columns

### Analytics Indexes
- Market cap filtering: `idx_stock_data_market_cap`
- Sector/industry analysis: `idx_stock_data_sector`, `idx_stock_data_industry`
- Top movers: `idx_*_chg_percentage`, `idx_*_volume`, `idx_*_float_rotation`
- Short interest: `idx_stock_short_data_short_percent`

### Composite Indexes
- Stock history: `idx_ticker_history_stock_date`
- Recent news: `idx_stock_news_stock_time`

## Verification

After setup, verify the installation:

```sql
-- Check schemas
SELECT schema_name FROM information_schema.schemata
WHERE schema_name IN ('equities', 'pre_market', 'regular_market', 'after_market', 'schwab_access');

-- Check tables
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema IN ('equities', 'pre_market', 'regular_market', 'after_market', 'schwab_access')
ORDER BY table_schema, table_name;

-- Check foreign keys
SELECT
    tc.constraint_name,
    tc.table_schema,
    tc.table_name,
    kcu.column_name,
    ccu.table_schema AS foreign_table_schema,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.table_schema, tc.table_name;

-- Check indexes
SELECT
    schemaname,
    tablename,
    indexname
FROM pg_indexes
WHERE schemaname IN ('equities', 'pre_market', 'regular_market', 'after_market', 'schwab_access')
ORDER BY schemaname, tablename, indexname;
```

## Configuration

After database setup, configure your application connection:

### Environment Variables

```bash
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="trading"
export DB_USER="your_username"
export DB_PASSWORD="your_password"
```

### Application Configuration

Update your database connection settings in the application to match your PostgreSQL setup.

See the main project [README.md](../../README.md) for complete setup instructions.

## Troubleshooting

### Error: "database already exists"

If you want to recreate the database:
```bash
# Drop and recreate manually
psql -U postgres -c "DROP DATABASE trading;"
psql -U postgres -c "CREATE DATABASE trading;"

# Then run setup_all.sql again
cd db/schema
psql -U postgres -d trading -f setup_all.sql
```

### Error: "permission denied"

Ensure your PostgreSQL user has sufficient privileges:
```sql
GRANT ALL PRIVILEGES ON DATABASE trading TO your_username;
```

### Error: "could not connect to server"

Check PostgreSQL is running:
```bash
# Linux
sudo systemctl status postgresql

# macOS
brew services list

# Check connection
psql -U postgres -d postgres -c "SELECT 1;"
```

### Error: "extension does not exist"

The `uuid-ossp` extension requires PostgreSQL contrib package:
```bash
# Ubuntu/Debian
sudo apt-get install postgresql-contrib

# macOS (Homebrew)
# Usually included with PostgreSQL installation
```

## Backup and Restore

### Backup

```bash
pg_dump -U postgres -d trading -F c -b -v -f trading_backup.dump
```

### Restore

```bash
pg_restore -U postgres -d trading -v trading_backup.dump
```

## Next Steps

After database setup:

1. Configure database connection in your application
2. Set up Schwab API credentials (see main README.md)
3. Run the scanner: `python main.py`

## Support

For issues or questions:
- Check the main project [README.md](../../README.md)
- Review the [ERD diagram](../../docs/erd_diagram.png)
- Open an issue on GitHub
