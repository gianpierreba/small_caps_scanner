"""
External API clients for market data retrieval

This module contains:
- SchwabAPI: Official Schwab market data API client
- SearchYahooFinance: Yahoo Finance wrapper using yfinance
- AlphaVantage: Alpha Vantage API client for top gainers and losers
- PolygonAPI: Polygon.io API client for top gainers
- FMPApi: Financial Modeling Prep API client for biggest gainers
- AlpacaAPI: Alpaca API client for most actively traded stocks and top market movers
- IntrinioAPI: Intrinio API client for market data about top gainers/losers
"""
from db.scanners_db import RetrieveData, InsertData
from polygon.rest.models import TickerSnapshot
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from helpers.helpers import Helpers
from polygon import RESTClient
from typing import Optional
import yfinance as yf
import webbrowser
import requests
import logging
import base64
import uuid
import os

# Log configuration
LOGGER = logging.getLogger(__name__)


# ============================================================================
# CHARLES SCHWAB API
# ============================================================================

class SchwabAPI:
    """
    Charles Schwab API client for market data
    Sign up at https://developer.schwab.com/

    Features:
    - Top gainers/losers by stock exchange
    - Real-time market data
    - Comprehensive fundamental data
    - Professional-grade data quality
    - OAuth2 authentication
    - Automatic token refresh
    - Web-based user authentication flow
    - Secure storage of access and refresh tokens
    - Integration with local database for token management
    - Support for multiple stock tickers
    """

    APP_KEY_SCHWAB = os.getenv('APP_KEY_SCHWAB')
    CLIENT_SECRET_SCHWAB = os.getenv('CLIENT_SECRET_SCHWAB')

    def __init__(self, access_token: str = None, stock_ticker: str = None):
        """
        Initialize SchwabAPI client, set up authentication and optionally load market data for a given stock ticker

        :param access_token: OAuth access token for Schwab API authentication
        :type access_token: str
        :param stock_ticker: Stock ticker symbol to fetch market data for
        :type stock_ticker: str
        """
        self.schwab_access = 'schwab_access.schwab_access_refresh_token'
        self.market_data_base_url = 'https://api.schwabapi.com/marketdata/v1'
        self.redirect_uri = 'https://127.0.0.1'
        self.session = requests.Session()
        self.access_token = access_token
        self.token_expiry = None

        # Initialize dependencies
        self.inserter = InsertData()
        self.retriever = RetrieveData()

        if self.access_token is None:
            self.access_token, self.token_expiry = self.get_access_token()

        self.headers = {
            'accept': 'application/json',
            'Authorization': f"Bearer {self.access_token}"
        }

        if stock_ticker is not None:
            self.stock_ticker = stock_ticker
            self._quote_single = self.quote_single(
                stock_ticker=self.stock_ticker)
            self._stock_fundamental = self.stock_fundamental(
                stock_ticker=self.stock_ticker)
        else:
            self.stock_ticker = None

    def get_access_token(self):
        """
        Retrieve a valid access token, refreshing or authenticating if necessary

        Returns:
            Tuple of access token and its expiry time
        """
        if self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token, self.token_expiry

        if self._30_minutes_passed():
            if self._has_week_passed():
                self._authenticate()
                token_data = self._retrieve_latest_token()
                return token_data['access_token'], token_data['expiry_time']
            else:
                token_data = self._retrieve_latest_token()
                if self._is_token_valid(token_data['access_token']):
                    return token_data['access_token'], token_data['expiry_time']
                else:
                    refreshed_token_data = self._refresh_tokens()
                    if refreshed_token_data:
                        return refreshed_token_data['access_token'], refreshed_token_data['expiry_time']
                    else:
                        self._authenticate()
                        token_data = self._retrieve_latest_token()
                        return token_data['access_token'], token_data['expiry_time']
        else:
            token_data = self._retrieve_latest_token()
            return token_data['access_token'], token_data['expiry_time']

    def _has_week_passed(self, timestamp_str: str = None):
        if timestamp_str is None:
            data_date = self.retriever.retrieve_data(
                table_name="schwab_access.schwab_access_refresh_token", column="time")[-1][0]
        else:
            data_date = datetime.fromisoformat(timestamp_str)
        return (datetime.now() - data_date) >= timedelta(weeks=1)

    def _30_minutes_passed(self) -> bool:
        data_token = self.retriever.retrieve_data(
            table_name="schwab_access.schwab_access_refresh_token", column="time")[-1]
        return (datetime.now() - data_token[0]) >= timedelta(minutes=30)

    def _is_token_valid(self, access_token: str) -> bool:
        headers = {'accept': 'application/json',
                   'Authorization': f"Bearer {access_token}"}
        response = self.session.get(
            url=self.market_data_base_url + '/FFIE/quotes', headers=headers)
        return response.status_code == 200

    def _retrieve_latest_token(self) -> dict:
        token_data = self.retriever.retrieve_data(
            table_name="schwab_access.schwab_access_refresh_token", column="*")[-1]
        return {
            'access_token': token_data[6],
            'expiry_time': token_data[1] + timedelta(seconds=token_data[2])
        }

    def _construct_init_auth_url(self) -> str:
        auth_url = f"https://api.schwabapi.com/v1/oauth/authorize?client_id={self.__class__.APP_KEY_SCHWAB}&redirect_uri={self.redirect_uri}"
        LOGGER.info(f"Click to authenticate: {auth_url}")
        return auth_url

    def _construct_headers_and_payload(self, returned_url: str) -> tuple:
        response_code = f"{returned_url[returned_url.index('code=') + 5: returned_url.index('%40')]}@"
        credentials = f"{self.__class__.APP_KEY_SCHWAB}:{self.__class__.CLIENT_SECRET_SCHWAB}"
        base64_credentials = base64.b64encode(
            credentials.encode("utf-8")).decode("utf-8")

        headers = {
            "Authorization": f"Basic {base64_credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        payload = {
            "grant_type": "authorization_code",
            "code": response_code,
            "redirect_uri": self.redirect_uri,
        }
        return headers, payload

    def _retrieve_tokens(self, headers: dict, payload: dict) -> dict:
        response = self.session.post(
            url="https://api.schwabapi.com/v1/oauth/token", headers=headers, data=payload)
        return response.json()

    def _authenticate(self):
        auth_url = self._construct_init_auth_url()
        webbrowser.open(auth_url)
        LOGGER.info("Paste Returned URL:")
        returned_url = input()
        headers, payload = self._construct_headers_and_payload(returned_url)
        tokens = self._retrieve_tokens(headers=headers, payload=payload)
        current_datetime = datetime.now()

        access_refresh_token_data = {
            'access_refresh_token_uuid': uuid.uuid4(),
            'time': current_datetime,
            'expires_in': tokens['expires_in'],
            'token_type': tokens['token_type'],
            'scope': tokens['scope'],
            'refresh_token': tokens['refresh_token'],
            'access_token': tokens['access_token'],
            'id_token': tokens['id_token']
        }
        self.inserter.insert_data(
            table=self.schwab_access, data=access_refresh_token_data)
        return tokens

    def _refresh_tokens(self):
        refresh_token = self.retriever.retrieve_data(
            table_name="schwab_access.schwab_access_refresh_token", column="refresh_token")[-1][0]
        payload = {"grant_type": "refresh_token",
                   "refresh_token": refresh_token}
        headers = {
            "Authorization": f'Basic {base64.b64encode(f"{self.__class__.APP_KEY_SCHWAB}:{self.__class__.CLIENT_SECRET_SCHWAB}".encode()).decode()}',
            "Content-Type": "application/x-www-form-urlencoded"
        }
        response = self.session.post(
            url="https://api.schwabapi.com/v1/oauth/token", headers=headers, data=payload)

        if response.status_code == 200:
            tokens = response.json()
            current_datetime = datetime.now()
            access_refresh_token_data = {
                'access_refresh_token_uuid': uuid.uuid4(),
                'time': current_datetime,
                'expires_in': tokens['expires_in'],
                'token_type': tokens['token_type'],
                'scope': tokens['scope'],
                'refresh_token': tokens['refresh_token'],
                'access_token': tokens['access_token'],
                'id_token': tokens['id_token']
            }
            self.inserter.insert_data(
                table=self.schwab_access, data=access_refresh_token_data)
            return {
                'access_token': tokens['access_token'],
                'expiry_time': current_datetime + timedelta(seconds=tokens['expires_in'])
            }
        else:
            LOGGER.error(f"Error refreshing access token: {response.text}")
            return None

    def movers(self, symbol_id: str, sort: str) -> dict:
        api_url = f"{self.market_data_base_url}/movers/{symbol_id}?sort={sort}"
        response = requests.get(api_url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            return {
                'status_code': response.status_code,
                'message': 'Failed to retrieve data',
                'content': response.text
            }

    def market_cap(self, stock_ticker: str = None) -> float:
        stock_fundamental = self._stock_fundamental if self.stock_ticker else self.stock_fundamental(
            stock_ticker)
        return stock_fundamental['instruments'][0]['fundamental']['marketCap']

    def average_volume(self, output: int, stock_ticker: str = None):
        stock_fundamental = self._stock_fundamental if self.stock_ticker else self.stock_fundamental(
            stock_ticker)

        volume_map = {
            1: 'avg1DayVolume',
            10: 'avg10DaysVolume',
            30: 'avg3MonthVolume'
        }
        key = volume_map.get(output)
        return stock_fundamental['instruments'][0]['fundamental'][key] if key else None

    def stock_fundamental(self, stock_ticker: str = None):
        ticker = self.stock_ticker if self.stock_ticker else stock_ticker
        api_url = f"{self.market_data_base_url}/instruments?symbol={ticker}&projection=fundamental"
        response = requests.get(api_url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            return {
                'status_code': response.status_code,
                'message': 'Failed to retrieve data',
                'content': response.text
            }

    def quote_single(self, stock_ticker: str = None):
        if stock_ticker is not None:
            api_url = f"{self.market_data_base_url}/{stock_ticker}/quotes"
            response = requests.get(api_url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'status_code': response.status_code,
                    'message': 'Failed to retrieve data',
                    'content': response.text
                }
        elif self.stock_ticker is not None:
            return self._quote_single
        else:
            raise ValueError(
                "stock_ticker needed in constructor or as parameter")

    def last_price(self, stock_ticker: str = None) -> Optional[float]:
        if stock_ticker is not None:
            request = self.quote_single(stock_ticker=stock_ticker)
            try:
                return request[stock_ticker]['quote']['lastPrice']
            except KeyError:
                return None
        else:
            try:
                return self._quote_single[self.stock_ticker]['quote']['lastPrice']
            except KeyError:
                return None

    def change_percentage(self, stock_ticker: str = None) -> Optional[float]:
        if stock_ticker is not None:
            request = self.quote_single(stock_ticker=stock_ticker)
            try:
                return request[stock_ticker]['quote']['netPercentChange']
            except KeyError:
                return None
        else:
            try:
                return self._quote_single[self.stock_ticker]['quote']['netPercentChange']
            except KeyError:
                return None

    def volume(self, stock_ticker: str = None) -> Optional[float]:
        if stock_ticker is not None:
            request = self.quote_single(stock_ticker=stock_ticker)
            return request[stock_ticker]['quote']['totalVolume']
        else:
            return self._quote_single[self.stock_ticker]['quote']['totalVolume']

    def quote_time(self, stock_ticker: str = None) -> datetime:
        helper = Helpers()
        if stock_ticker:
            quote_data = self.quote_single(stock_ticker=stock_ticker)
        else:
            quote_data = self._quote_single[self.stock_ticker]

        try:
            quote_time = quote_data['quote']['quoteTime']
        except KeyError as e:
            raise KeyError(f"Missing key in quote data: {e}")

        return helper.detect_and_convert_timestamp(timestamp=quote_time)

    def company_name(self, stock_ticker: str = None) -> Optional[str]:
        if stock_ticker is not None:
            request = self.quote_single(stock_ticker=stock_ticker)
            try:
                return request[stock_ticker]['reference']['description']
            except KeyError:
                return None
        else:
            try:
                return self._quote_single[self.stock_ticker]['reference']['description']
            except KeyError:
                return None


# ============================================================================
# YAHOO FINANCE API
# ============================================================================

class SearchYahooFinance:
    """Yahoo Finance API wrapper with lazy loading"""

    def __init__(self, ticker: str = None, company_name: str = None):
        self.ticker = ticker
        self.company_name = company_name
        self.yahoo_finance_api = None
        self.yahoo_finance_api_info = None

    def _initialize_api(self):
        if not self.yahoo_finance_api and self.ticker:
            self.yahoo_finance_api = yf.Ticker(self.ticker)
            self.yahoo_finance_api_info = self.yahoo_finance_api.info

    def _get_info(self, key):
        self._initialize_api()
        return self.yahoo_finance_api_info.get(key, None)

    def company_country(self):
        return self._get_info('country')

    def website(self):
        return self._get_info('website')

    def business_summary(self):
        return self._get_info('longBusinessSummary')

    def short_ratio_date(self):
        return self._get_info('dateShortInterest')

    def industry(self):
        return self._get_info('industry')

    def sector(self):
        return self._get_info('sector')

    def operating_cash_flow(self):
        return self._get_info('operatingCashflow')

    def shares_short(self):
        return self._get_info('sharesShort')

    def shares_short_previous_month_date(self):
        return self._get_info('sharesShortPreviousMonthDate')

    def shares_short_prior_month(self):
        return self._get_info('sharesShortPriorMonth')

    def shares_percent_shares_outstanding(self):
        return self._get_info('sharesPercentSharesOut')

    def short_percent_float(self):
        return self._get_info('shortPercentOfFloat')

    def short_ratio(self):
        return self._get_info('shortRatio')

    def avg_volume_10d(self):
        return self._get_info('averageVolume10days')

    def avg_volume_3m(self):
        return self._get_info('averageVolume')

    def held_institutions(self):
        return self._get_info('heldPercentInstitutions')

    def held_insiders(self):
        return self._get_info('heldPercentInsiders')

    def market_cap(self):
        return self._get_info('marketCap')

    def stock_float(self):
        return self._get_info('floatShares')

    def company_news(self):
        self._initialize_api()
        return self.yahoo_finance_api.news


# ============================================================================
# ALPHA VANTAGE API
# ============================================================================

class AlphaVantageAPI:
    """
    Alpha Vantage API client for top gainers - FREE SERVICE
    This is a FREE API service. Sign up at https://www.alphavantage.co/support/#api-key
    Features:
    - Top gainers and losers stock tickers
    """

    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

    def __init__(self, api_key: str = None):
        """
        Initialize Alpha Vantage API client
        Args:
            api_key: Your Alpha Vantage API key (optional, defaults to env variable)
        """
        self.api_key = api_key or self.__class__.ALPHA_VANTAGE_API_KEY

        if not self.api_key:
            raise ValueError(
                "Alpha Vantage API key required. Set ALPHA_VANTAGE_API_KEY environment variable or pass api_key parameter"
            )

        self.base_url = 'https://www.alphavantage.co/query'
        self.session = requests.Session()
        # HTML Basic Auth with API key as username
        self.session.auth = (self.api_key, '')

    def _make_request(
        self,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated request to Alpha Vantage API

        Args:
            params: Query parameters

        Returns:
            JSON response as dictionary

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        try:
            response = self.session.get(
                self.base_url,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                LOGGER.error("Invalid Alpha Vantage API key")
            elif response.status_code == 400:
                LOGGER.error("One of the request parameters is invalid")
            elif response.status_code == 403:
                LOGGER.error("Access forbidden - check your subscription plan")
            elif response.status_code == 429:
                LOGGER.error("Rate limit exceeded")
            elif response.status_code == 500:
                LOGGER.error("Internal server error at Alpha Vantage")
            else:
                LOGGER.error(f"HTTP error: {e}")
            raise

        except requests.exceptions.RequestException as e:
            LOGGER.error(f"Request failed: {e}")
            raise

    def get_top_gainers_losers(self) -> list[str]:
        """
        Fetches top gaining stock tickers from Alpha Vantage API.

        Returns:
            list[str]: List of ticker symbols for top gainers.
                    Returns empty list if API call fails.
        """

        params = {
            'function': 'TOP_GAINERS_LOSERS',
            'apikey': self.api_key,
        }

        try:
            data = self._make_request(params=params)

            # Extract top gainers list
            top_gainers_list = data.get('top_gainers', [])

            # Return list of tickers only
            return [stock['ticker'] for stock in top_gainers_list if 'ticker' in stock]

        except requests.exceptions.Timeout:
            print("API request timed out")
            return []
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return []
        except (KeyError, ValueError) as e:
            print(f"Error parsing API response: {e}")
            return []


# ============================================================================
# POLYGON API
# ============================================================================

class PolygonAPI:
    """
    Polygon.io API client for top gainers and top market movers - PAID SERVICE
    This is a PAID API service. Sign up at https://polygon.io/pricing
    Features:
    - Top gainers stock tickers
    """

    POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')

    def __init__(self, api_key: str = None):
        """
        Initialize Polygon API client
        Args:
            api_key: Your Polygon API key (optional, defaults to env variable)
        """
        self.api_key = api_key or self.__class__.POLYGON_API_KEY

        if not self.api_key:
            raise ValueError(
                "Polygon API key required. Set POLYGON_API_KEY environment variable or pass api_key parameter"
            )

        self.client = RESTClient(self.api_key)

    def get_top_gainers(self) -> list[str]:
        """
        Fetches top gaining stock tickers from Polygon API.
        Returns:
            list[str]: List of ticker symbols for top gainers.
                       Returns empty list if API call fails.
        """
        try:
            tickers = self.client.get_snapshot_direction(
                "stocks",
                direction="gainers"
            )

            result = []
            for item in tickers:
                # Verify this is a TickerSnapshot and a float
                if isinstance(item, TickerSnapshot) and isinstance(item.todays_change_percent, float):
                    result.append(item.ticker)

            return result

        except Exception as e:
            print(f"Error fetching top gainers: {e}")
            return []


# ============================================================================
# FINANCIAL MODELING PREP (FMP) API
# ============================================================================

class FMPApi:
    """
    Financial Modeling Prep (FMP) API client for market data - FREE and PAID SERVICE

    This is a FREE and PAID API service. Sign up at https://financialmodelingprep.com/developer/docs/pricing/

    Features:
    - Top gainers/losers by stock exchange
    """

    FMP_API_KEY = os.getenv('FMP_API_KEY')

    def __init__(self, api_key: str = None):
        """
        Initialize FMP API client

        Args:
            api_key: Your FMP API key (optional, defaults to env variable)
        """
        self.api_key = api_key or self.__class__.FMP_API_KEY
        if not self.api_key:
            raise ValueError(
                "FMP API key required. Set FMP_API_KEY environment variable or pass api_key parameter"
            )
        self.base_url = 'https://financialmodelingprep.com/stable'
        self.session = requests.Session()
        # HTTP Basic Auth with API key as username
        self.session.auth = (self.api_key, '')

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated request to FMP API

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            JSON response as dictionary

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                LOGGER.error("Invalid FMP API key")
            elif response.status_code == 400:
                LOGGER.error("One of the request parameters is invalid")
            elif response.status_code == 403:
                LOGGER.error("Access forbidden - check your subscription plan")
            elif response.status_code == 429:
                LOGGER.error("Rate limit exceeded")
            elif response.status_code == 500:
                LOGGER.error("Internal server error at FMP")
            else:
                LOGGER.error(f"HTTP error: {e}")
            raise

        except requests.exceptions.RequestException as e:
            LOGGER.error(f"Request failed: {e}")
            raise

    def get_biggest_gainers(self) -> list[str]:
        '''
        Fetches top gaining stock tickers from FMP API.
        Returns:
            list[str]: List of ticker symbols for top gainers.
                    Returns empty list if API call fails.
        '''
        endpoint = f'/biggest-gainers?apikey={self.__class__.FMP_API_KEY}'

        try:
            data = self._make_request(endpoint=endpoint)

            # Return list of tickers only
            return [stock['symbol'] for stock in data if 'symbol' in stock]

        except requests.exceptions.Timeout:
            print("API request timed out")
            return []
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return []
        except (KeyError, ValueError) as e:
            print(f"Error parsing API response: {e}")
            return []


# ============================================================================
# ALPACA API
# ============================================================================

class AlpacaAPI:
    """
    Alpaca API client for market data - PAID SERVICE

    This is a PAID API service. Sign up at https://alpaca.markets/docs/api-documentation/api-v2/market-data/

    Features:
    - Top gainers and losers by stock exchange
    - Most actively traded stocks
    """

    ALPACA_CLIENT_ID = os.getenv('ALPACA_CLIENT_ID')
    ALPACA_CLIENT_SECRET = os.getenv('ALPACA_CLIENT_SECRET')

    def __init__(self, alpaca_client_id: str = None, alpaca_client_secret: str = None):
        """
        Initialize Alpaca API client
        Args:
            api_key: Your Alpaca API key (optional, defaults to env variable)
        """
        self.alpaca_client_id = alpaca_client_id or self.__class__.ALPACA_CLIENT_ID

        if not alpaca_client_id:
            raise ValueError(
                "Alpaca Client ID required. Set ALPACA_CLIENT_ID environment variable or pass alpaca_client_id parameter"
            )

        self.alpaca_client_secret = alpaca_client_secret or self.__class__.ALPACA_CLIENT_SECRET

        if not alpaca_client_secret:
            raise ValueError(
                "Alpaca Client Secret required. Set ALPACA_CLIENT_SECRET environment variable or pass alpaca_client_secret parameter"
            )

        self.base_url = 'https://data.alpaca.markets/v1beta1'
        self.session = requests.Session()
        # HTTP Basic Auth with API key as username
        self.session.auth = (self.api_key, '')

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated request to Alpaca API

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            JSON response as dictionary

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        url = f"{self.base_url}{endpoint}"

        headers = {
            "accept": "application/json",
            "APCA-API-KEY-ID": self.alpaca_client_id,
            "APCA-API-SECRET-KEY": self.alpaca_client_secret
        }

        try:
            response = self.session.get(
                url,
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                LOGGER.error("Invalid Alpaca API key")
            elif response.status_code == 400:
                LOGGER.error("One of the request parameters is invalid")
            elif response.status_code == 403:
                LOGGER.error("Access forbidden - check your subscription plan")
            elif response.status_code == 429:
                LOGGER.error("Rate limit exceeded")
            elif response.status_code == 500:
                LOGGER.error("Internal server error at Alpaca")
            else:
                LOGGER.error(f"HTTP error: {e}")
            raise

        except requests.exceptions.RequestException as e:
            LOGGER.error(f"Request failed: {e}")
            raise

    def top_market_movers(
        self,
        market_type: str = 'stocks',
        top: int = 10
    ) -> list[str]:
        '''
        Fetches top gaining stock tickers from Alpaca API.

        Args:
            market_type: Type of market ('stocks' or 'crypto') (default: 'stocks')
            top: Number of top movers to retrieve (default: 10)

        Returns:
            List of ticker symbols for top gainers

        Example:
            >>> api = Alpaca()
            >>> gainers = api.top_market_movers(
            ...     market_type='stocks', 
            ...     top=10
            ... )
            >>> print(gainers)
            ['AAPL', 'TSLA', 'NVDA', ...]
        '''
        endpoint = f"/screener/{market_type}/movers"

        params = {
            'top': top,
        }

        try:
            data = self._make_request(
                endpoint=endpoint,
                params=params
            )
            raw_result = data.get('gainers', [])

            # Return list of tickers only
            return [stock['symbol'] for stock in raw_result if 'symbol' in stock]

        except requests.exceptions.Timeout:
            print("API request timed out")
            return []
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return []
        except (KeyError, ValueError) as e:
            print(f"Error parsing API response: {e}")
            return []

    def most_active_stocks(
        self,
        by: str = 'volume',
        top: int = 10
    ) -> list[str]:
        '''
        Fetches most actively traded stock tickers from Alpaca API.
        Args:
            by: Criteria to sort by ('volume' or 'trades') (default: 'volume')
            top: Number of top most active stocks to fetch per day (default: 10)
        Returns:
            List of ticker symbols for most active stocks
        Example:
            >>> api = Alpaca()
            >>> active_stocks = api.most_active_stocks(
            ...     by='volume',
            ...     top=10
            ... )
            >>> print(active_stocks)
            ['AAPL', 'TSLA', 'NVDA', ...]
        '''
        endpoint = f"/screener/stocks/most-actives?by={by}?top={top}"

        try:
            data = self._make_request(endpoint=endpoint)
            raw_result = data.get('most_actives', [])

            # Return list of tickers only
            return [stock['symbol'] for stock in raw_result if 'symbol' in stock]

        except requests.exceptions.Timeout:
            print("API request timed out")
            return []
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return []
        except (KeyError, ValueError) as e:
            print(f"Error parsing API response: {e}")
            return []


# ============================================================================
# INTRINIO API
# ============================================================================

class IntrinioAPI:
    """
    Intrinio API client for market data - PAID SERVICE

    This is a PAID API service. Sign up at https://intrinio.com/signup

    Features:
    - Top gainers and losers by stock exchange
    """

    INTRINIO_API_KEY = os.getenv('INTRINIO_API_KEY')

    def __init__(self, api_key: str = None):
        """
        Initialize Intrinio API client

        Args:
            api_key (string, optional): Your Intrinio API key. Defaults to 'INTRINIO_API_KEY' env variable.
        """
        self.api_key = api_key or self.__class__.INTRINIO_API_KEY

        if not self.api_key:
            raise ValueError(
                "Intrinio API key required. Set INTRINIO_API_KEY environment variable or pass api_key parameter"
            )

        self.base_url = 'https://api-v2.intrinio.com'
        self.session = requests.Session()
        # HTTP Basic Auth with API key as username
        self.session.auth = (self.api_key, '')

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated request to Intrinio API

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            JSON response as dictionary

        Raises:
            requests.exceptions.RequestException: If request fails
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                LOGGER.error("Invalid Intrinio API key")
            elif response.status_code == 403:
                LOGGER.error("Access forbidden - check your subscription plan")
            elif response.status_code == 429:
                LOGGER.error("Rate limit exceeded")
            else:
                LOGGER.error(f"HTTP error: {e}")
            raise

        except requests.exceptions.RequestException as e:
            LOGGER.error(f"Request failed: {e}")
            raise

    def get_stock_exchange_gainers(
        self,
        identifier: str = 'USCOMP',
        min_price: Optional[float] = None,
        page_size: int = 100,
        source: Optional[str] = None
    ) -> List[str]:
        """
        Get top gaining securities tickers for a stock exchange

        Args:
            identifier: Stock exchange identifier. Options:
                - 'USCOMP' (US Composite - all US exchanges, default)
                - 'XNYS' (New York Stock Exchange)
                - 'XNAS' (NASDAQ)
                - 'XASE' (NYSE American)
                - 'ARCX' (NYSE Arca)
                - 'IEXG' (IEX)
            min_price: Minimum stock price filter (e.g., 5.0 for $5+)
            page_size: Number of results (max 10000)
            source: Specific data source (optional)

        Returns:
            List of ticker symbols for top gainers

        Example:
            >>> api = IntrinioAPI()
            >>> gainers = api.get_stock_exchange_gainers(
            ...     identifier='USCOMP', 
            ...     min_price=5
            ... )
            >>> print(gainers[:10])
            ['AAPL', 'TSLA', 'NVDA', ...]
        """
        endpoint = f'/stock_exchanges/{identifier}/gainers'

        params = {
            'page_size': page_size
        }

        if min_price is not None:
            params['min_price'] = min_price

        if source is not None:
            params['source'] = source

        try:
            data = self._make_request(endpoint, params)
            securities = data.get('securities', [])

            # Extract just the ticker symbols
            tickers = []
            for security in securities:
                security_info = security.get('security', {})
                ticker = security_info.get('ticker')
                if ticker:
                    tickers.append(ticker)

            LOGGER.info(
                f"Retrieved {len(tickers)} gainers from {identifier}"
            )
            return tickers

        except Exception as e:
            LOGGER.error(f"Error fetching gainers: {e}")
            return []

    def get_stock_exchange_losers(
        self,
        identifier: str = 'USCOMP',
        min_price: Optional[float] = None,
        page_size: int = 100,
        source: Optional[str] = None
    ) -> List[str]:
        """
        Get top losing securities tickers for a stock exchange

        Args:
            identifier: Stock exchange identifier (see get_stock_exchange_gainers)
            min_price: Minimum stock price filter
            page_size: Number of results (max 10000)
            source: Specific data source (optional)

        Returns:
            List of ticker symbols for top losers
        """
        endpoint = f'/stock_exchanges/{identifier}/losers'

        params = {
            'page_size': page_size
        }

        if min_price is not None:
            params['min_price'] = min_price

        if source is not None:
            params['source'] = source

        try:
            data = self._make_request(endpoint, params)
            securities = data.get('securities', [])

            # Extract just the ticker symbols
            tickers = []
            for security in securities:
                security_info = security.get('security', {})
                ticker = security_info.get('ticker')
                if ticker:
                    tickers.append(ticker)

            LOGGER.info(
                f"Retrieved {len(tickers)} losers from {identifier}"
            )
            return tickers

        except Exception as e:
            LOGGER.error(f"Error fetching losers: {e}")
            return []
