"""
Utilities and helper functions for the scanner module

This module contains:
- Data structures (StockQuoteData, NewsItem)
- Searching utility class
- Helper functions
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from helpers.helpers import Helpers

from .apis import SearchYahooFinance

# ============================================================================
# DATA STRUCTURES
# ============================================================================


@dataclass
class StockQuoteData:
    """Data structure for stock quotes"""

    last_price: Optional[float] = None
    change_percentage: Optional[float] = None
    volume: Optional[float] = None
    quote_time: Optional[datetime] = None
    company_name: Optional[str] = None
    market_cap: Optional[float] = None
    avg_vol_1_day: Optional[float] = None
    avg_vol_10_day: Optional[float] = None
    avg_vol_3_month: Optional[float] = None


@dataclass
class NewsItem:
    """Data structure for news items"""

    uuid_news: str
    title: str
    publisher: str
    link: str
    publish_time: str
    content_type: str
    related_tickers: Optional[List[str]] = None


# ============================================================================
# UTILITY CLASSES
# ============================================================================


class Searching:
    """Utility class for searching stock information"""

    def __init__(self, stock_ticker: str):
        self.stock_ticker = stock_ticker

    def search_stock(self):
        """Search and display stock information from Yahoo Finance"""
        helper = Helpers()
        search = SearchYahooFinance(ticker=self.stock_ticker)

        print("---- ---- " * 4)
        print(f"Ticker -> {self.stock_ticker}")

        stock_float = (
            helper.format_number(search.stock_float()) if search.stock_float() else None
        )
        market_cap = (
            helper.format_number(search.market_cap()) if search.market_cap() else None
        )
        held_insiders = (
            helper.format_percentage(search.held_insiders())
            if search.held_insiders()
            else None
        )
        held_institutions = (
            helper.format_percentage(search.held_institutions())
            if search.held_institutions()
            else None
        )
        avg_vol_3_month = (
            helper.format_number(search.avg_volume_3m())
            if search.avg_volume_3m()
            else None
        )
        avg_vol_10_day = (
            helper.format_number(search.avg_volume_10d())
            if search.avg_volume_10d()
            else None
        )

        print(f"Stock Float -> {stock_float}")
        print(f"Market Cap -> {market_cap}")
        print(f"Held by Insiders -> {held_insiders}")
        print(f"Held by Institutions -> {held_institutions}")
        print(f"Avg Vol (3 month) -> {avg_vol_3_month}")
        print(f"Avg Vol (10 day) -> {avg_vol_10_day}")
        print(f"Short Ratio -> {search.short_ratio()}")
        print(f"Sector -> {search.sector()}")
        print(f"Industry -> {search.industry()}")

        company_news = search.company_news()
        for position, news in enumerate(company_news, start=1):
            print("---- ---- " * 2)
            print(f"- News {position} / UUID: {news.get('uuid', news.get('id'))}")
            print(f"- News {position} / Title: {news.get('title', 'N/A')}")
            print(f"- News {position} / Publisher: {news.get('publisher', 'N/A')}")

        print("---- ---- " * 4)
