"""
Database Module
===============

PostgreSQL database operations for the Stock Market Scanner.

Provides connection pooling and CRUD operations for:
- Stock data (equities schema)
- Short interest data
- Company news
- Scanner results (pre/regular/after market)
- Schwab API tokens

Classes:
    DatabaseConnection: Thread-safe connection pool management
    InsertData: Insert operations with automatic commits
    RetrieveData: Query operations with parameterized queries
    UpdateData: Update operations with WHERE clauses

Example:
    >>> from db import RetrieveData
    >>> retriever = RetrieveData()
    >>> data = retriever.retrieve_data(
    ...     table_name="equities.stock_data",
    ...     condition_column="ticker",
    ...     condition_value="AAPL"
    ... )
"""

from .scanners_db import (
    DatabaseConnection,
    InsertData,
    RetrieveData,
    UpdateData
)

__all__ = [
    'DatabaseConnection',
    'InsertData',
    'RetrieveData',
    'UpdateData'
]
