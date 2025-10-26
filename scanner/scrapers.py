"""
Web scrapers for different market data sources

This module contains:
- ScanStockAnalysis: Scraper for StockAnalysis.com

⚠️ WARNING: These scrapers may violate the Terms of Service of the target websites.
Users are solely responsible for ensuring compliance with all applicable ToS.
See LICENSE and README.md for full legal disclaimers.
"""
from bs4 import BeautifulSoup
import requests
import warnings
import logging

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ============================================================================
# WEB SCRAPERS
# ============================================================================

# Headers for web scraping
HEADER = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15'
}


class ScanStockAnalysis:
    """
    Web scraper for StockAnalysis.com with lazy loading

    ⚠️ NOTE: StockAnalysis.com's robots.txt allows crawlers and their Terms
    do not explicitly prohibit scraping. However, you must comply with their
    content attribution requirement: "you can use snippets of the content as
    long as you do not modify the content and clearly state where you got it from."

    Attribution: Data sourced from https://stockanalysis.com/
    """

    def __init__(self):
        # Issue informational warning on instantiation
        warnings.warn(
            "\n" + "="*80 + "\n"
            "⚠️  NOTICE: StockAnalysis.com Web Scraper\n"
            "="*80 + "\n"
            "You are using a web scraper for StockAnalysis.com.\n\n"
            "REQUIREMENTS:\n"
            "  • You MUST attribute data to https://stockanalysis.com/\n"
            "  • Do NOT modify the scraped content\n"
            "  • Do NOT republish full content without permission\n\n"
            "RECOMMENDATION:\n"
            "  Consider using official APIs for more reliable data:\n"
            "  - Charles Schwab (FREE)\n"
            "  - Alpha Vantage (FREE tier available)\n"
            "  - See README.md for ToS-compliant alternatives\n\n"
            "BY CONTINUING, YOU AGREE TO COMPLY WITH ATTRIBUTION REQUIREMENTS.\n"
            "="*80,
            UserWarning,
            stacklevel=2
        )
        logger.info("ScanStockAnalysis scraper initialized - Remember to attribute data source")

        self._name_lines_premarket_gainers = None
        self._name_lines_regular_market_gainers = None
        self._name_lines_regular_market_active = None

    def _initialize_premarket_gainers(self):
        if not self._name_lines_premarket_gainers:
            url = "https://stockanalysis.com/markets/premarket/"
            response = requests.get(url, headers=HEADER)
            soup = BeautifulSoup(response.text, "html.parser")
            self._name_lines_premarket_gainers = soup.find(
                "table", class_="symbol-table svelte-1ro3niy", attrs={"id": "main-table"}
            ).find("tbody").find_all("tr", class_="svelte-1ro3niy")

    def _initialize_regular_market(self, data_type):
        if data_type == 'gainers' and not self._name_lines_regular_market_gainers:
            url = "https://stockanalysis.com/markets/gainers/"
            response = requests.get(url, headers=HEADER)
            soup = BeautifulSoup(response.text, "html.parser")
            self._name_lines_regular_market_gainers = soup.find(
                "table", class_="symbol-table svelte-1ro3niy", attrs={"id": "main-table"}
            ).find("tbody").find_all("tr", class_="svelte-1ro3niy")

        elif data_type == 'active' and not self._name_lines_regular_market_active:
            url = "https://stockanalysis.com/markets/active/"
            response = requests.get(url, headers=HEADER)
            soup = BeautifulSoup(response.text, "html.parser")
            self._name_lines_regular_market_active = soup.find(
                "table", class_="symbol-table svelte-1ro3niy", attrs={"id": "main-table"}
            ).find("tbody").find_all("tr", class_="svelte-1ro3niy")

    def _get_premarket_gainer_info(self, position: int, column: int):
        self._initialize_premarket_gainers()
        return self._name_lines_premarket_gainers[position].find_all("td")[column].get_text(strip=True)

    def _get_regular_market_info(self, position: int, column: int, data_type: str):
        self._initialize_regular_market(data_type)
        if data_type == 'gainers':
            return self._name_lines_regular_market_gainers[position].find_all("td")[column].get_text(strip=True)
        elif data_type == 'active':
            return self._name_lines_regular_market_active[position].find_all("td")[column].get_text(strip=True)

    def regular_market_length(self, data_type: str):
        self._initialize_regular_market(data_type)
        if data_type == 'gainers':
            return len(self._name_lines_regular_market_gainers)
        elif data_type == 'active':
            return len(self._name_lines_regular_market_active)

    def premarket_gainers_length(self):
        self._initialize_premarket_gainers()
        return len(self._name_lines_premarket_gainers)

    def ticker(self, position: int, market: str, data_type: str = None):
        if market == 'pre_market' and data_type is None:
            return self._get_premarket_gainer_info(position, 1)
        elif market == 'regular_market':
            if data_type is None:
                raise ValueError(
                    "'data_type' must be provided for 'regular_market'")
            return self._get_regular_market_info(position=position, column=1, data_type=data_type)
        else:
            raise ValueError(
                "market must be either 'pre_market' or 'regular_market'")
