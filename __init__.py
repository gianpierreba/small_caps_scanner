"""
Stock Market Scanner
====================

A comprehensive stock market scanner that tracks movers across pre-market,
regular market, and after-market trading sessions.

Features:
- Multi-source data aggregation (Schwab API, Yahoo Finance, StockAnalysis)
- PostgreSQL database integration with automated setup
- Multi-threaded concurrent scanning
- Configurable via .env files
- Professional database schema with 40+ performance indexes

Quick Start:
    >>> from scanner import PreMarket
    >>> scanner = PreMarket(output_length=15)
    >>> scanner.stock_analysis()

Documentation: https://github.com/gianpierreba/small_caps_scanner
"""

from __version__ import __version__, __version_info__

__author__ = "Gianpierre Benites"
__license__ = "MIT"
__all__ = ['__version__', '__version_info__']
