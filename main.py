from scanner.executor import start_scanner_thread, stop_all_scanners
from scanner.config import MarketType
from scanner.utilities import Searching
from config import config, validate_config
from __version__ import __version__
import signal
import sys
import time


def searching_ticker(stock_ticker: str):
    """
    General information of a publicly traded company
    """
    search_stock = Searching(stock_ticker=stock_ticker)
    search_stock.search_stock()


def signal_handler(sig, frame):
    """Handle SIGINT (Ctrl+C) to stop all scanners gracefully."""
    print("\nStopping all scanners...")
    stop_all_scanners()
    sys.exit(0)


def display_tos_warning_and_get_consent():
    """
    Display Terms of Service warning and require explicit user consent.
    Returns True if user consents, False otherwise.
    """
    warning_message = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║                     ⚠️  CRITICAL LEGAL WARNING ⚠️                             ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝

THIS SOFTWARE INCLUDES WEB SCRAPING FUNCTIONALITY FOR:

  • StockAnalysis.com (robots.txt allows crawling, but requires attribution)

═══════════════════════════════════════════════════════════════════════════════

⚠️  YOUR RESPONSIBILITIES:

  • MUST provide attribution to StockAnalysis.com when using their data
  • Do NOT modify scraped content
  • Do NOT republish full content without permission
  • Monitor for HTTP 403/429 errors and stop if blocked

═══════════════════════════════════════════════════════════════════════════════

✅ RECOMMENDED ALTERNATIVES - USE OFFICIAL APIs INSTEAD:

This project already includes integrations for ToS-compliant APIs:
  • Charles Schwab API (FREE)
  • Alpha Vantage (FREE tier available)
  • Polygon.io (PAID)
  • Financial Modeling Prep (FREE tier available)
  • Alpaca Markets (FREE tier available)

See README.md for detailed setup instructions.

═══════════════════════════════════════════════════════════════════════════════

📋 DISCLAIMERS:

  • This software is for EDUCATIONAL and RESEARCH purposes only
  • NOT financial advice or investment recommendations
  • Authors accept NO liability for your use of this software
  • You are SOLELY responsible for all legal consequences

═══════════════════════════════════════════════════════════════════════════════

BY TYPING 'I AGREE' BELOW, YOU ACKNOWLEDGE THAT:

  1. You have read and understand the LICENSE file
  2. You have read and understand the README.md legal warnings
  3. You will provide attribution to StockAnalysis.com for their data
  4. You will NOT hold the authors liable for any consequences
  5. You understand the benefits of using official APIs over web scraping

═══════════════════════════════════════════════════════════════════════════════
"""

    print(warning_message)
    print("\nTo continue, type 'I AGREE' (case-sensitive) and press Enter.")
    print("To exit, type anything else or press Ctrl+C.\n")

    try:
        user_input = input("Your response: ").strip()

        if user_input == "I AGREE":
            print("\n✓ Consent recorded. Starting scanners...\n")
            time.sleep(2)  # Give user time to read the confirmation
            return True
        else:
            print("\n✗ Consent not provided. Exiting for your legal protection.")
            print("Consider using the official API integrations instead (see README.md).\n")
            return False

    except KeyboardInterrupt:
        print("\n\n✗ Consent not provided. Exiting for your legal protection.")
        print("Consider using the official API integrations instead (see README.md).\n")
        return False


if __name__ == "__main__":
    # Display version
    print(f"Stock Market Scanner v{__version__}")
    print("=" * 50)
    print()

    # Validate configuration on startup
    print("Validating configuration...")
    try:
        validate_config(require_schwab=True)
        print("✓ Configuration is valid\n")

        # Print configuration summary
        config.print_summary()
        print()

    except ValueError as e:
        print(f"\n✗ Configuration Error:\n{e}\n")
        print("Please check your .env file or environment variables.")
        print("See .env.example for configuration template.\n")
        sys.exit(1)

    # Display Terms of Service warning and get explicit consent
    if not display_tos_warning_and_get_consent():
        sys.exit(0)

    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    # Use configured sleep time
    sleep_time = config.app.sleep_time

    """Start scanner"""
    # ============================================================================
    # SCANNER THREAD CONFIGURATION
    # ============================================================================
    # By default, both Pre-Market and Regular Market scanners run simultaneously.
    #
    # To run only specific scanners:
    # 1. Comment out the scanner(s) you DON'T want to run (add # at line start)
    # 2. Keep uncommented the scanner(s) you DO want to run
    # 3. Run: python main.py
    #
    # Example: To run ONLY Pre-Market scanner, comment out Regular-Market below
    # ============================================================================

    # Pre-Market Scanners - ACTIVE
    # Comment this out if you only want Regular Market scanner
    start_scanner_thread(market_type=MarketType.PRE_MARKET,
                         sleep_time=sleep_time)

    # Regular-Market Scanners - ACTIVE
    # Comment this out if you only want Pre-Market scanner
    start_scanner_thread(market_type=MarketType.REGULAR_MARKET,
                         sleep_time=sleep_time)

    # After-Market Scanners - DISABLED (UNDER DEVELOPMENT)
    # ⚠️ NOTICE: After-market scanner is incomplete and currently disabled
    # The implementation uses regular-market data instead of proper after-market data
    # Will be enabled in a future release once properly implemented
    #
    # start_scanner_thread(market_type=MarketType.AFTER_MARKET,
    #                      sleep_time=sleep_time)

    print("Scanners running. Press Ctrl+C to stop.")
    print("⚠️  REMINDER: Remember to attribute data to StockAnalysis.com")
    print("    Monitor for HTTP 403/429 errors and stop immediately if blocked.")
    print("\nℹ️  NOTE: After-market scanner is currently under development and disabled.\n")

    # Keep the main thread alive
    signal.pause()

    """Search for a specific stock ticker"""
    # stock_ticker = ''
    # searching_ticker(stock_ticker=stock_ticker)
