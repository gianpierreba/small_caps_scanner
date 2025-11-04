"""
Scanner Configuration Module

This module provides configuration classes and utilities for the stock market scanner.
It defines market types, scanner configurations, and factory functions for creating
scanner instances.

Classes:
    MarketType: Enum representing different market sessions (pre-market, regular, after-market)
    ScannerConfig: Dataclass holding configuration for each scanner type

Functions:
    get_scanner_configs: Factory function that returns scanner configurations

Note:
    The module uses lazy imports in get_scanner_configs() to avoid circular
    import dependencies between scanner modules.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List


class MarketType(Enum):
    """Enum to represent different market types"""

    PRE_MARKET = "pre_market"
    REGULAR_MARKET = "regular_market"
    AFTER_MARKET = "after_market"


@dataclass
class ScannerConfig:
    """Configuration for each scanner type"""

    market_type: MarketType
    scanner_class: type
    active_scanners: List[str]


def get_scanner_configs():
    """
    Factory function to create configurations.
    Lazy import to avoid circular imports.

    NOTE: AfterMarket scanner is currently under development and disabled.
    The MarketType.AFTER_MARKET enum remains for database schema compatibility.
    """
    from .scanner import PreMarket, RegularMarket  # pylint: disable=import-outside-toplevel

    # AfterMarket is commented out - under development

    return {
        MarketType.PRE_MARKET: ScannerConfig(
            market_type=MarketType.PRE_MARKET,
            scanner_class=PreMarket,
            active_scanners=[
                "charles_schwab_pre_market_movers",
                "stock_analysis",
            ],
        ),
        MarketType.REGULAR_MARKET: ScannerConfig(
            market_type=MarketType.REGULAR_MARKET,
            scanner_class=RegularMarket,
            active_scanners=[
                "charles_schwab_regular_market_movers",
                "stock_analysis_regular_market_gainers",
                "stock_analysis_regular_market_active",
            ],
        ),
        # ⚠️ AFTER_MARKET: UNDER DEVELOPMENT - Configuration disabled
        # The implementation is incomplete and will be enabled in a future release
        #
        # MarketType.AFTER_MARKET: ScannerConfig(
        #     market_type=MarketType.AFTER_MARKET,
        #     scanner_class=AfterMarket,
        #     active_scanners=[
        #         'charles_schwab_after_market_movers',
        #         'stock_analysis_after_market_gainers',
        #         'stock_analysis_after_market_active',
        #     ]
        # )
    }
