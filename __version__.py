"""
Version information for Stock Market Scanner
"""

__version__ = "0.1.0"
__version_info__ = (0, 1, 0)

# Version history
VERSION_HISTORY = {
    "0.1.0": {
        "date": "2025-10-26",
        "changes": [
            "Initial release",
            "Multi-market scanning (pre-market, regular, after-market)",
            "Schwab API integration",
            "Yahoo Finance integration",
            "StockAnalysis.com web scraping",
            "PostgreSQL database with ERD",
            "Configuration management via .env",
            "Cross-platform database setup (SQL scripts)",
        ],
        "breaking_changes": [],
    }
}


def get_version():
    """Get current version string"""
    return __version__


def get_version_info():
    """Get current version as tuple"""
    return __version_info__
