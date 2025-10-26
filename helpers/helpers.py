from db.scanners_db import RetrieveData, UpdateData
from datetime import datetime
from decimal import Decimal
import requests

RETRIEVE = RetrieveData()
UPDATE_DATA = UpdateData()


class Helpers():
    def __init__(self) -> None:
        pass

    def search_ticker(self, company_name: str) -> str:
        if not company_name:
            return None

        # Helper to search and extract ticker symbols
        def get_tickers(company_name):
            yfinance = "https://query2.finance.yahoo.com/v1/finance/search"
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
            params = {"q": company_name}
            res = requests.get(url=yfinance,
                               params=params,
                               headers={'User-Agent': user_agent})
            data = res.json()

            try:
                return data['quotes'][0]['symbol']
            except IndexError:
                return None

        # First try with the full name
        tickers = get_tickers(company_name=company_name)
        if tickers:
            return tickers

        # Try shorter variations by removing common suffixes
        suffixes = ["Corp", "Corporation", "Inc", "PLC", "Plc", "Ltd"]
        name_parts = company_name.split()
        while name_parts:
            if name_parts[-1] in suffixes:
                name_parts.pop()  # Remove suffix
            query = " ".join(name_parts)
            tickers = get_tickers(query)
            if tickers:
                return tickers
            name_parts.pop()  # Try with one less word each time

        return None

    def format_number(self, num):
        """
        This function is designed to convert a numerical value (either an integer or a float)
        into a human-readable string with appropriate suffixes ("K" for thousands, "M" for millions, "B" for billions, etc.).
        """
        if num is None:
            return "--"  # Return a placeholder for None values
        try:
            # Ensure the number is a float for consistent formatting
            num = float(num)
        except (ValueError, TypeError):
            return "--"  # Handle cases where conversion fails

        # Format the number based on its size
        if abs(num) >= 1_000_000_000:
            formatted_num = f"{num / 1_000_000_000:.2f} B"
        elif abs(num) >= 1_000_000:
            formatted_num = f"{num / 1_000_000:.2f} M"
        elif abs(num) >= 1_000:
            formatted_num = f"{num / 1_000:.2f} K"
        else:
            # For numbers below 1,000, show with two decimal points
            formatted_num = f"{num:.2f}"
        return formatted_num

    def format_percentage(self, value):
        """
        The format_percentage function is intended to convert a float value into a percentage string, formatted to two decimal places.
        """
        if value is None:
            return "--"  # Return a placeholder for None values
        try:
            # Ensure the number is a float for consistent formatting
            value = float(value)
        except (ValueError, TypeError):
            return "--"  # Handle cases where conversion fails
        # Format the number as a percentage
        return f"{value * 100:.2f} %"

    def detect_and_convert_timestamp(self, timestamp: int | float, resultado: str = "date") -> str | datetime:
        """
        Detects whether a given timestamp is in Unix format (seconds) or in milliseconds, and converts it to a readable date.

        Args:
            timestamp (int or float): The timestamp to be detected and converted.
            resultado (str): The 'return' of the function.

        Returns:
            str: timestamp type.
            datetime: A readable date and time.
        """
        # Convert the timestamp to a string to check its length
        if timestamp is None:
            return None
        else:
            timestamp_str = str(timestamp)

            # Determine the type of timestamp and convert accordingly
            if len(timestamp_str) == 10:
                # It's a Unix timestamp (seconds)
                date_time = datetime.fromtimestamp(timestamp)
                timestamp_type = "Unix timestamp (seconds)"
            elif len(timestamp_str) == 13:
                # It's a timestamp in milliseconds
                timestamp_s = timestamp / 1000.0
                date_time = datetime.fromtimestamp(timestamp_s)
                timestamp_type = "Timestamp in milliseconds"
            else:
                raise ValueError("Unknown timestamp format")

            # Return the readable date and time
            if resultado == 'date':
                return date_time
            elif resultado == 'type':
                return timestamp_type
            else:
                msg = "Invalid value for 'resultado'. Choose 'date' or 'type'."
                raise ValueError(msg)

    def convert_percentage_to_numeric(self, percentage_str):
        # Remove the percentage sign
        percentage_str = percentage_str.strip('%')

        # Convert to float and divide by 100 to get the numeric value
        numeric_value = float(percentage_str) / 100

        return numeric_value

    def convert_string_to_numeric(self, value):
        try:
            if "%" in value:
                # Handle percentage strings
                return float(value.strip('%')) / 100
            elif "." in value:
                # Handle decimal strings
                return Decimal(value)
            else:
                # Handle integer strings
                return int(value)
        except ValueError as e:
            print(f"Error converting value: {e}")
            return None

    def _get_cik(self, ticker: str) -> str | None:
        """
        The function retrieves the Central Index Key (CIK) number for a given company's ticker symbol.

        Parameters:
        -----------
        ticker : str
            The stock ticker symbol of the company for which you want to retrieve the CIK. The ticker is case-insensitive (e.g., "AAPL" for Apple Inc.).

        Returns:
        --------
        str
            The CIK number as a string if the ticker is found in the SEC's company list.
        None
            Returns None if the ticker is not found or if there is an issue fetching or parsing the data.
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15'
        }
        tickers_json = requests.get(
            url="https://www.sec.gov/files/company_tickers.json",
            headers=headers).json()
        for company in tickers_json.values():
            if company["ticker"] == ticker:
                return company["cik_str"]

    def _get_and_update_cik(self, stock_ticker: str):
        # Retrieve cik_number from the database for the given market
        cik_number = RETRIEVE.retrieve_data(table_name='equities.stock_data',
                                            column='cik_number',
                                            condition_column='ticker',
                                            condition_value=stock_ticker)

        # If cik_number exists, return it
        if cik_number[0][0] is not None:
            return cik_number[0][0]

        # If cik_number does not exist, fetch it and update the database
        cik_number = self._get_cik(ticker=stock_ticker)

        # Update cik_number in the database for the given market
        update_data_params = {'cik_number': cik_number}
        UPDATE_DATA.update_data(table='equities.stock_data',
                                update_data=update_data_params,
                                where_constraint_column='ticker',
                                where_constraint_data=stock_ticker)

        return cik_number

    def cik_number(self, stock_ticker: str, search_ticker: bool = False):
        '''Looking for CIK Number'''

        # If search_ticker is False, use the database; otherwise, search for cik_number
        if not search_ticker:
            return self._get_and_update_cik(stock_ticker)

        # If search_ticker is True, directly fetch cik_number
        cik_number = self._get_cik(ticker=stock_ticker)
        return str(cik_number)


class DBHelpers():
    def __init__(self) -> None:
        pass

    def get_tickers_in_db(self, market: str = None) -> list:
        """
        Retrieve the list of tickers from the specified market's database table.

        Args:
            market (str, optional): The market category. Options are "pre_market", 
                                    "regular_market", "after_market", or None (for "equities").

        Returns:
            list: A list of tickers found in the database for the specified market.

        Raises:
            ValueError: If the market name is invalid.
        """
        # Define valid markets and their corresponding table names
        valid_markets = {
            None: "equities.stock_data",
            "pre_market": "pre_market.pre_market_scanner",
            "regular_market": "regular_market.regular_market_scanner",
            "after_market": "after_market.after_market_scanner",
        }

        # Validate the market and retrieve the table name
        table_name = valid_markets.get(market)
        if table_name is None and market is not None:
            msg_value_error = f"Invalid market: {market}. Must be one of {list(valid_markets.keys())[1:]} or None."
            raise ValueError(msg_value_error)

        # Retrieve tickers from the database
        data = RETRIEVE.retrieve_data(column="ticker", table_name=table_name)

        # Return the list of tickers
        return [row[0] for row in data]

    def get_uuid(self, ticker: str, market: str) -> str:
        """
        Retrieve the UUID for a given ticker from the specified market's table.

        Args:
            ticker (str): The ticker symbol.
            market (str): The market category. Options are "equities", "pre_market", "regular_market", or "after_market".

        Returns:
            str: The UUID associated with the ticker.

        Raises:
            ValueError: If the market name is invalid.
            LookupError: If no UUID is found for the ticker.
        """
        # Define valid markets and corresponding table names
        valid_markets = {
            "equities": "equities.stock_data",
            "pre_market": "pre_market.pre_market_scanner",
            "regular_market": "regular_market.regular_market_scanner",
            "after_market": "after_market.after_market_scanner",
        }

        # Validate the market
        if market not in valid_markets:
            msg_value_error = f"Invalid market: {market}. Must be one of {list(valid_markets.keys())}."
            raise ValueError(msg_value_error)

        # Fetch the table name based on the market
        table_name = valid_markets[market]

        # Retrieve the UUID
        uuid_raw = RETRIEVE.retrieve_data(
            column="stock_uuid",
            table_name=table_name,
            condition_column="ticker",
            condition_value=ticker,
        )

        # Handle cases where no UUID is found
        if not uuid_raw:
            msg_look_up_error = f"No UUID found for ticker '{ticker}' in market '{market}'."
            raise LookupError(msg_look_up_error)

        return uuid_raw[0]
