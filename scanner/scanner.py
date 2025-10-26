"""
Core scanner logic and market-specific scanner classes

This module contains:
- Scanner: Base class with core scanning logic
- ScannerCore: Orchestrates the scanning process
- StockDataFetcher: Fetches data from APIs
- NewsProcessor: Processes company news
- TickerHistoryManager: Manages ticker history
- PreMarket: Pre-market scanner implementation (WORKING)
- RegularMarket: Regular market scanner implementation (WORKING)
- AfterMarket: After market scanner implementation (UNDER DEVELOPMENT - Commented out)
"""
from db.scanners_db import RetrieveData, UpdateData, InsertData
from .scrapers import ScanStockAnalysis
from .apis import SchwabAPI, SearchYahooFinance
from .utilities import StockQuoteData, NewsItem
from helpers.helpers import Helpers, DBHelpers
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import uuid

LOGGER = logging.getLogger(__name__)


# ============================================================================
# DATA FETCHING AND PROCESSING
# ============================================================================

class StockDataFetcher:
    """Handles fetching data from various APIs"""

    def __init__(self, helper: Helpers):
        """Initialize StockDataFetcher with helper utilities."""
        self.helper = helper

    def fetch_schwab_quote_data(self,
                                stock_ticker: str
                                ) -> StockQuoteData:
        """
        Fetch basic quote data from Schwab API.
        
        Parameters:
        - stock_ticker: The ticker symbol of the stock.
        Returns: StockQuoteData object with basic quote information.
        
        Example:
        - Fetches quote data for AAPL
            quote_data = fetch_schwab_quote_data("AAPL")
        """
        try:
            api = SchwabAPI(stock_ticker=stock_ticker)
            return StockQuoteData(
                last_price=api.last_price(),
                change_percentage=api.change_percentage(),
                volume=api.volume(),
                quote_time=api.quote_time()
            )
        except (KeyError, Exception) as e:
            LOGGER.warning(
                f"Error fetching Schwab quote data for {stock_ticker}: {e}")
            return StockQuoteData(quote_time=datetime.now())

    def fetch_schwab_full_data(self, stock_ticker: str) -> StockQuoteData:
        """Fetch complete data including fundamentals from Schwab API"""
        try:
            api = SchwabAPI(stock_ticker=stock_ticker)
            return StockQuoteData(
                company_name=api.company_name(),
                last_price=api.last_price(),
                change_percentage=api.change_percentage(),
                volume=api.volume(),
                quote_time=api.quote_time(),
                avg_vol_1_day=api.average_volume(output=1),
                avg_vol_10_day=api.average_volume(output=10),
                avg_vol_3_month=api.average_volume(output=30),
                market_cap=api.market_cap()
            )
        except (KeyError, Exception) as e:
            LOGGER.warning(
                f"Error fetching full Schwab data for {stock_ticker}: {e}")
            return StockQuoteData(quote_time=datetime.now())

    def fetch_yahoo_data(self, stock_ticker: str) -> Dict[str, Any]:
        """Fetch additional data from Yahoo Finance"""
        scan = SearchYahooFinance(ticker=stock_ticker)

        return {
            'company_country': scan.company_country(),
            'business_website': scan.website(),
            'business_summary': scan.business_summary(),
            'stock_float': scan.stock_float(),
            'held_insiders': scan.held_insiders(),
            'held_institutions': scan.held_institutions(),
            'operating_cash_flow': scan.operating_cash_flow(),
            'sector': scan.sector(),
            'industry': scan.industry(),
            'short_ratio': scan.short_ratio(),
            'shares_short': scan.shares_short(),
            'short_percent_float': scan.short_percent_float(),
            'shares_percent_shares_outstanding': scan.shares_percent_shares_outstanding(),
            'shares_short_prior_month': scan.shares_short_prior_month(),
            'shares_short_previous_month_date': scan.shares_short_previous_month_date(),
            'short_ratio_date': scan.short_ratio_date()
        }

    def parse_news_item(self, news: Dict) -> Optional[NewsItem]:
        """Parse a news item from Yahoo Finance API"""
        try:
            return NewsItem(
                uuid_news=news['id'],
                title=news['content']['title'].strip(),
                publisher=news['content']['provider']['displayName'],
                link=news['content']['canonicalUrl']['url'],
                publish_time=datetime.fromisoformat(
                    news['content']['pubDate'].replace('Z', '+00:00')
                ).strftime('%Y-%m-%d %H:%M:%S'),
                content_type=news['content']['contentType'],
                related_tickers=news.get('relatedTickers')
            )
        except KeyError as e:
            LOGGER.error(f"Error parsing news item: {e}")
            return None


class NewsProcessor:
    """Handles company news processing and storage"""

    def __init__(self, inserter: InsertData, retriever: RetrieveData, fetcher: StockDataFetcher):
        """
        Initialize NewsProcessor with database inserter, retriever, and data fetcher.
        """
        self.inserter = inserter
        self.retriever = retriever
        self.fetcher = fetcher

    def process_company_news(self,
                             stock_ticker: str,
                             stock_uuid: str,
                             company_news: List[Dict]
                             ) -> None:
        """
        Process and insert company news into the database.
        
        Parameters:
        - stock_ticker: The ticker symbol of the stock.
        - stock_uuid: The UUID of the stock in the database.
        - company_news: A list of news items fetched from Yahoo Finance.
        
        Returns: None
        
        Example:
        - Processes and inserts news for a given stock ticker
            process_company_news("AAPL", "some-uuid", news_list)
        """
        for news_dict in company_news:
            news = self.fetcher.parse_news_item(news_dict)
            if not news:
                continue

            # Check if news already exists
            existing_news_uuids = self.retriever.retrieve_data(
                column="uuid_news",
                table_name="equities.stock_news",
                condition_column="stock_uuid",
                condition_value=stock_uuid
            )

            if news.uuid_news in {str(row[0]) for row in existing_news_uuids}:
                continue

            # Insert new news
            news_data = {
                'stock_uuid': stock_uuid,
                'ticker': stock_ticker,
                'uuid_news': news.uuid_news,
                'title': news.title,
                'publisher': news.publisher,
                'link': news.link,
                'publish_time': news.publish_time,
                'type': news.content_type,
                'related_tickers': news.related_tickers,
            }

            self.inserter.insert_data(
                table='equities.stock_news',
                data=news_data
            )
            print(f"Inserted news for '{stock_ticker}' -> {news.title[:50]}...")


class TickerHistoryManager:
    """Manages ticker history records"""

    def __init__(self, inserter: InsertData, retriever: RetrieveData):
        self.inserter = inserter
        self.retriever = retriever

    def add_today_if_needed(self, stock_uuid: str, stock_ticker: str, quote_time: datetime):
        """Add today's date to ticker_history if not already present"""
        existing_dates = self.retriever.retrieve_data(
            column="date",
            table_name="equities.ticker_history",
            condition_column="stock_uuid",
            condition_value=stock_uuid
        )

        if datetime.now().date() not in {row[0] for row in existing_dates}:
            history_data = {
                'ticker_history_uuid': uuid.uuid4(),
                'stock_uuid': stock_uuid,
                'date': quote_time.date(),
                'week': quote_time.isocalendar()[1]
            }
            self.inserter.insert_data(
                table='equities.ticker_history', data=history_data)
            print(f"Added ticker history for '{stock_ticker}'")


# ============================================================================
# CORE SCANNER LOGIC
# ============================================================================

class ScannerCore:
    """Core scanner logic - orchestrates the scanning process"""

    def __init__(self, inserter: InsertData, retriever: RetrieveData,
                 updater: UpdateData, helper: Helpers):
        self.inserter = inserter
        self.retriever = retriever
        self.updater = updater
        self.helper = helper
        self.db_helper = DBHelpers()

        # Initialize sub-components
        self.fetcher = StockDataFetcher(helper)
        self.news_processor = NewsProcessor(inserter, retriever, self.fetcher)
        self.history_manager = TickerHistoryManager(inserter, retriever)

    def scan_ticker(self, stock_ticker: str, scanner_table: str, market: str,
                    market_type: str, source: str, position: int):
        """Main scanner entry point"""
        print(
            f"---- << {market_type} >> '{stock_ticker}' from '{source}' ({position}) ----")

        tickers_in_db = self.db_helper.get_tickers_in_db()

        if stock_ticker in tickers_in_db:
            self._update_existing_ticker(stock_ticker, scanner_table, market)
        else:
            self._add_new_ticker(stock_ticker, scanner_table)

    def _update_existing_ticker(self, stock_ticker: str, scanner_table: str, market: str):
        """Handle existing ticker update logic"""
        print(f"... Updating -> '{stock_ticker}'")

        quote_time_db = self.retriever.retrieve_data(
            column="quote_time",
            table_name="equities.stock_data",
            condition_column="ticker",
            condition_value=stock_ticker
        )[0][0]

        stock_uuid = self.db_helper.get_uuid(
            ticker=stock_ticker, market='equities')

        if self._is_same_date_as_today(quote_time_db):
            self._update_today_data(
                stock_ticker, scanner_table, market, stock_uuid)
        else:
            self._update_stale_data(stock_ticker, scanner_table, stock_uuid)

    def _update_today_data(self, stock_ticker: str, scanner_table: str,
                           market: str, stock_uuid: str):
        """Update data that's already current for today"""
        tickers_in_scanner = self.db_helper.get_tickers_in_db(market=market)
        quote_data = self.fetcher.fetch_schwab_quote_data(stock_ticker)

        if stock_ticker in tickers_in_scanner:
            self._update_scanner_table(scanner_table, stock_uuid, quote_data)
            print(f"... Updated scanner table for '{stock_ticker}'")
        else:
            self._insert_scanner_table(scanner_table, stock_ticker, quote_data)
            self.history_manager.add_today_if_needed(
                stock_uuid, stock_ticker, quote_data.quote_time)

            scan = SearchYahooFinance(ticker=stock_ticker)
            self.news_processor.process_company_news(
                stock_ticker, stock_uuid, scan.company_news()
            )

        print(f"---- " * 8)

    def _update_stale_data(self, stock_ticker: str, scanner_table: str, stock_uuid: str):
        """Update data that's outdated (not from today)"""
        schwab_data = self.fetcher.fetch_schwab_full_data(stock_ticker)
        yahoo_data = self.fetcher.fetch_yahoo_data(stock_ticker)

        self._update_stock_data_table(stock_uuid, schwab_data, yahoo_data)
        self._update_short_data_table(stock_uuid, yahoo_data)
        self.history_manager.add_today_if_needed(
            stock_uuid, stock_ticker, schwab_data.quote_time)

        quote_data = StockQuoteData(
            last_price=schwab_data.last_price,
            change_percentage=schwab_data.change_percentage,
            volume=schwab_data.volume,
            quote_time=schwab_data.quote_time
        )
        self._insert_scanner_table(scanner_table, stock_ticker, quote_data)

        scan = SearchYahooFinance(ticker=stock_ticker)
        self.news_processor.process_company_news(
            stock_ticker, stock_uuid, scan.company_news()
        )

        print(f"---- " * 8)

    def _add_new_ticker(self, stock_ticker: str, scanner_table: str):
        """Add completely new ticker to database"""
        print(f"- Adding new stock -> {stock_ticker}")

        schwab_data = self.fetcher.fetch_schwab_full_data(stock_ticker)
        yahoo_data = self.fetcher.fetch_yahoo_data(stock_ticker)
        stock_uuid = uuid.uuid4()

        self._insert_stock_data_table(
            stock_uuid, stock_ticker, schwab_data, yahoo_data)
        self._insert_short_data_table(stock_uuid, stock_ticker, yahoo_data)
        self.history_manager.add_today_if_needed(
            stock_uuid, stock_ticker, schwab_data.quote_time)

        quote_data = StockQuoteData(
            last_price=schwab_data.last_price,
            change_percentage=schwab_data.change_percentage,
            volume=schwab_data.volume,
            quote_time=schwab_data.quote_time
        )
        self._insert_scanner_table(scanner_table, stock_ticker, quote_data)

        scan = SearchYahooFinance(ticker=stock_ticker)
        self.news_processor.process_company_news(
            stock_ticker, str(stock_uuid), scan.company_news()
        )

        print(f"---- " * 8)

    # Database operation helpers
    def _update_scanner_table(self, table: str, stock_uuid: str, data: StockQuoteData):
        update_params = {
            'quote_time': data.quote_time,
            'last_price': data.last_price,
            'chg_percentage': data.change_percentage,
            'volume': data.volume
        }
        self.updater.update_data(
            table=table, update_data=update_params,
            where_constraint_column='stock_uuid',
            where_constraint_data=stock_uuid
        )

    def _insert_scanner_table(self, table: str, ticker: str, data: StockQuoteData):
        insert_params = {
            'quote_time': data.quote_time,
            'ticker': ticker,
            'last_price': data.last_price,
            'chg_percentage': data.change_percentage,
            'volume': data.volume
        }
        self.inserter.insert_data(table=table, data=insert_params)

    def _update_stock_data_table(self, stock_uuid: str, schwab: StockQuoteData, yahoo: Dict):
        update_params = {
            'quote_time': schwab.quote_time,
            'stock_float': yahoo['stock_float'],
            'market_cap': schwab.market_cap,
            'held_insiders': yahoo['held_insiders'],
            'held_institutions': yahoo['held_institutions'],
            'avg_one_day_volume': schwab.avg_vol_1_day,
            'avg_vol_ten_days': schwab.avg_vol_10_day,
            'avg_vol_three_months': schwab.avg_vol_3_month,
            'operating_cash_flow': yahoo['operating_cash_flow'],
            'sector': yahoo['sector'],
            'industry': yahoo['industry'],
            'website': yahoo['business_website'],
            'country': yahoo['company_country'],
            'business_summary': yahoo['business_summary'],
        }
        self.updater.update_data(
            table='equities.stock_data', update_data=update_params,
            where_constraint_column='stock_uuid', where_constraint_data=stock_uuid
        )

    def _update_short_data_table(self, stock_uuid: str, yahoo: Dict):
        update_params = {
            'shares_short': yahoo['shares_short'],
            'short_ratio': yahoo['short_ratio'],
            'short_percent_float': yahoo['short_percent_float'],
            'shares_percent_shares_outstanding': yahoo['shares_percent_shares_outstanding'],
            'shares_short_prior_month': yahoo['shares_short_prior_month'],
            'short_ratio_date': self._convert_timestamp_if_needed(yahoo['short_ratio_date']),
            'shares_short_previous_month_date': self._convert_timestamp_if_needed(
                yahoo['shares_short_previous_month_date']
            )
        }
        self.updater.update_data(
            table='equities.stock_short_data', update_data=update_params,
            where_constraint_column='stock_uuid', where_constraint_data=stock_uuid
        )

    def _insert_stock_data_table(self, stock_uuid: uuid.UUID, ticker: str,
                                 schwab: StockQuoteData, yahoo: Dict):
        insert_params = {
            'stock_uuid': stock_uuid,
            'quote_time': schwab.quote_time,
            'ticker': ticker,
            'company_name': schwab.company_name,
            'stock_float': yahoo['stock_float'],
            'market_cap': schwab.market_cap,
            'held_insiders': yahoo['held_insiders'],
            'held_institutions': yahoo['held_institutions'],
            'avg_one_day_volume': schwab.avg_vol_1_day,
            'avg_vol_ten_days': schwab.avg_vol_10_day,
            'avg_vol_three_months': schwab.avg_vol_3_month,
            'operating_cash_flow': yahoo['operating_cash_flow'],
            'sector': yahoo['sector'],
            'industry': yahoo['industry'],
            'website': yahoo['business_website'],
            'country': yahoo['company_country'],
            'business_summary': yahoo['business_summary']
        }
        self.inserter.insert_data(
            table='equities.stock_data', data=insert_params)

    def _insert_short_data_table(self, stock_uuid: uuid.UUID, ticker: str, yahoo: Dict):
        insert_params = {
            'stock_uuid': stock_uuid,
            'ticker': ticker,
            'shares_short': yahoo['shares_short'],
            'short_ratio': yahoo['short_ratio'],
            'short_percent_float': yahoo['short_percent_float'],
            'shares_percent_shares_outstanding': yahoo['shares_percent_shares_outstanding'],
            'shares_short_prior_month': yahoo['shares_short_prior_month'],
            'short_ratio_date': self._convert_timestamp_if_needed(yahoo['short_ratio_date']),
            'shares_short_previous_month_date': self._convert_timestamp_if_needed(
                yahoo['shares_short_previous_month_date']
            )
        }
        self.inserter.insert_data(
            table='equities.stock_short_data', data=insert_params)

    def _convert_timestamp_if_needed(self, timestamp) -> Optional[datetime]:
        if timestamp is None:
            return None
        return self.helper.detect_and_convert_timestamp(timestamp=timestamp)

    def _is_same_date_as_today(self, input_datetime: datetime) -> bool:
        return input_datetime.date() == datetime.now().date()


# ============================================================================
# BASE SCANNER CLASS
# ============================================================================

class Scanner:
    """Base scanner class using composition"""

    def __init__(self):
        self.inserter = InsertData()
        self.retriever = RetrieveData()
        self.updater = UpdateData()
        self.helper = Helpers()

        # Delegate complex logic to ScannerCore
        self.core = ScannerCore(
            self.inserter, self.retriever, self.updater, self.helper
        )

    def scan_ticker(self, stock_ticker: str, scanner_table: str, market: str,
                    market_type: str, source: str, position: int):
        """Delegate to core scanner"""
        self.core.scan_ticker(
            stock_ticker, scanner_table, market, market_type, source, position
        )

    def is_same_date_as_today(self, input_datetime: datetime) -> bool:
        """Checks if the input datetime has the same date as today"""
        return input_datetime.date() == datetime.now().date()


# ============================================================================
# PRE-MARKET SCANNER
# ============================================================================

class PreMarket(Scanner):
    """Pre-market scanner implementation"""

    def __init__(self, output_length: str | int = None):
        super().__init__()
        self.output_length = output_length
        self.stock_analysis_scanner = ScanStockAnalysis()
        self.market = 'pre_market'
        self.market_type = 'Pre-Market'
        self.pre_market_scanner_table = 'pre_market.pre_market_scanner'

    def _get_length(self, total_length: int) -> int:
        """Helper to determine scan length"""
        if self.output_length is None:
            return 15
        elif self.output_length == 'total':
            return total_length
        else:
            return self.output_length

    def stock_analysis(self):
        """Premarket Gainers from StockAnalysis.com"""
        print(f"---- " * 8)
        length = self.stock_analysis_scanner.premarket_gainers_length()

        for i in range(length):
            stock_ticker = self.stock_analysis_scanner.ticker(
                position=i, market=self.market)
            try:
                self.scan_ticker(stock_ticker, self.pre_market_scanner_table,
                                 self.market, self.market_type, 'Stocks Analysis', i)
            except AttributeError:
                pass

    def charles_schwab_pre_market_movers(self, symbol_id: str = 'EQUITY_ALL',
                                         sort: str = 'PERCENT_CHANGE_UP'):
        """Screener from Charles Schwab"""
        print(f"---- " * 8)
        schwab = SchwabAPI()
        movers = schwab.movers(symbol_id=symbol_id, sort=sort)

        for position, ticker in enumerate(movers['screeners'], start=1):
            stock_ticker = ticker['symbol']
            self.scan_ticker(stock_ticker, self.pre_market_scanner_table,
                             self.market, self.market_type, 'Charles Schwab', position)


# ============================================================================
# REGULAR-MARKET SCANNER
# ============================================================================

class RegularMarket(Scanner):
    """Regular market scanner implementation"""

    def __init__(self, output_length: str | int = None):
        super().__init__()
        self.output_length = output_length
        self.stock_analysis_scanner = ScanStockAnalysis()
        self.market = "regular_market"
        self.market_type = "Regular-Market"
        self.regular_market_scanner_table = 'regular_market.regular_market_scanner'

    def _get_length(self, total_length: int) -> int:
        """Helper to determine scan length"""
        if self.output_length is None:
            return 15
        elif self.output_length == 'total':
            return total_length
        else:
            return self.output_length

    def stock_analysis_regular_market_gainers(self):
        """Regular Market Stocks Gainers from StockAnalysis.com"""
        print(f"---- " * 8)
        data_type = 'gainers'
        length = self.stock_analysis_scanner.regular_market_length(
            data_type=data_type)

        for i in range(length):
            stock_ticker = self.stock_analysis_scanner.ticker(
                position=i, market=self.market, data_type=data_type
            )
            self.scan_ticker(stock_ticker, self.regular_market_scanner_table,
                             self.market, self.market_type, 'Stocks Analysis - Gainers', i)

    def stock_analysis_regular_market_active(self):
        """Regular Market Stocks Active from StockAnalysis.com"""
        print(f"---- " * 8)
        data_type = 'active'
        length = self.stock_analysis_scanner.regular_market_length(
            data_type=data_type)

        for i in range(length):
            stock_ticker = self.stock_analysis_scanner.ticker(
                position=i, market=self.market, data_type=data_type
            )
            self.scan_ticker(stock_ticker, self.regular_market_scanner_table,
                             self.market, self.market_type, 'Stocks Analysis - Active', i)

    def charles_schwab_regular_market_movers(self, symbol_id: str = 'EQUITY_ALL',
                                             sort: str = 'PERCENT_CHANGE_UP'):
        """Screener from Charles Schwab in Regular Market"""
        print(f"---- " * 8)
        schwab = SchwabAPI()
        movers = schwab.movers(symbol_id=symbol_id, sort=sort)

        for position, ticker in enumerate(movers['screeners'], start=1):
            stock_ticker = ticker['symbol']
            self.scan_ticker(stock_ticker, self.regular_market_scanner_table,
                             self.market, self.market_type, 'Charles Schwab', position)


# ============================================================================
# AFTER-MARKET SCANNER - UNDER DEVELOPMENT
# ============================================================================
#
# ⚠️ NOTICE: After-market scanner is currently INCOMPLETE and UNDER DEVELOPMENT
#
# This scanner is not yet ready for production use. The implementation below
# has several issues:
# - Uses regular_market data/methods instead of after_market specific data
# - Scanner methods reference wrong market type ('regular_market' instead of 'after_market')
# - StockAnalysis.com scraper doesn't have dedicated after-market endpoints
# - Needs proper after-market specific data sources and validation
#
# Status: Will be deployed in a future release once proper after-market
#         data sources are identified and implemented.
#
# If you need after-market scanning, please use the PreMarket or RegularMarket
# scanners as reference implementations.
# ============================================================================

# class AfterMarket(Scanner):
#     """After market scanner implementation - UNDER DEVELOPMENT"""
#
#     def __init__(self, output_length: str | int = None):
#         super().__init__()
#         self.output_length = output_length
#         self.stock_analysis_scanner = ScanStockAnalysis()
#         self.market = "after_market"
#         self.market_type = "After-Market"
#         self.after_market_scanner_table = 'after_market.after_market_scanner'
#
#     def _get_length(self, total_length: int) -> int:
#         """Helper to determine scan length"""
#         if self.output_length is None:
#             return 15
#         elif self.output_length == 'total':
#             return total_length
#         else:
#             return self.output_length
#
#     def stock_analysis_after_market_gainers(self):
#         """After Market Stocks Gainers from StockAnalysis.com"""
#         print(f"---- " * 8)
#         data_type = 'gainers'
#         # ISSUE: Uses regular_market_length instead of after_market_length
#         length = self.stock_analysis_scanner.regular_market_length(
#             data_type=data_type)
#
#         for i in range(length):
#             # ISSUE: market='regular_market' should be 'after_market'
#             stock_ticker = self.stock_analysis_scanner.ticker(
#                 position=i, market='regular_market', data_type=data_type
#             )
#             self.scan_ticker(stock_ticker, self.after_market_scanner_table,
#                              self.market, self.market_type, 'Stocks Analysis - Gainers', i)
#
#     def stock_analysis_after_market_active(self):
#         """After Market Stocks Active from StockAnalysis.com"""
#         print(f"---- " * 8)
#         data_type = 'active'
#         # ISSUE: Uses regular_market_length instead of after_market_length
#         length = self.stock_analysis_scanner.regular_market_length(
#             data_type=data_type)
#
#         for i in range(length):
#             # ISSUE: market='regular_market' should be 'after_market'
#             stock_ticker = self.stock_analysis_scanner.ticker(
#                 position=i, market='regular_market', data_type=data_type
#             )
#             self.scan_ticker(stock_ticker, self.after_market_scanner_table,
#                              self.market, self.market_type, 'Stocks Analysis - Active', i)
#
#     def charles_schwab_after_market_movers(self, symbol_id: str = 'EQUITY_ALL',
#                                            sort: str = 'PERCENT_CHANGE_UP'):
#         """Screener from Charles Schwab in After Market"""
#         print(f"---- " * 8)
#         schwab = SchwabAPI()
#         movers = schwab.movers(symbol_id=symbol_id, sort=sort)
#
#         for position, ticker in enumerate(movers['screeners'], start=1):
#             stock_ticker = ticker['symbol']
#             self.scan_ticker(stock_ticker, self.after_market_scanner_table,
#                              self.market, self.market_type, 'Charles Schwab', position)
