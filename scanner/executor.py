"""
Scanner Executor Module

This module manages the execution and lifecycle of market scanners in separate threads.
It provides functions to start, stop, and monitor scanner threads for different market
sessions (pre-market, regular market, after-market).

Functions:
    execute_market_scanner: Main scanner execution loop
    start_scanner_thread: Start a scanner in a new thread
    stop_scanner: Stop a specific scanner thread
    stop_all_scanners: Stop all active scanner threads
    get_scanner_status: Get status of all running scanners
    log_message: Helper function for consistent logging

Global State:
    active_scanners: Dict tracking active scanner threads
    stop_events: Dict of threading.Event objects for stopping scanners
"""

import threading
import time
from datetime import datetime

from .config import MarketType, get_scanner_configs

# Global dictionaries to track active scanners
active_scanners = {}
stop_events = {}


def log_message(message: str, level: str = "INFO"):
    """Helper to log messages consistently"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def execute_market_scanner(
    market_type: MarketType, sleep_time: int, stop_event: threading.Event
) -> None:
    """
    Execute market scanners in a unified way.

    Args:
        market_type: market type (PRE_MARKET, REGULAR_MARKET, AFTER_MARKET)
        sleep_time: seconds between each scan cycle.
        stop_event: threading.Event to stop the scanner.
    """
    scanner_configs = get_scanner_configs()
    config = scanner_configs[market_type]
    scanner = config.scanner_class()

    log_message(f"Starting {market_type.value} scanner")

    while not stop_event.is_set():
        for scanner_method_name in config.active_scanners:
            if stop_event.is_set():
                break

            try:
                scanner_method = getattr(scanner, scanner_method_name)
                scanner_method()
            except AttributeError:
                log_message(f"Method '{scanner_method_name}' not found", level="ERROR")
            except (RuntimeError, ValueError, KeyError, TypeError) as e:
                log_message(f"Error in {scanner_method_name}: {str(e)}", level="ERROR")

        if not stop_event.is_set():
            log_message(f"Waiting {sleep_time} seconds till next update")
            time.sleep(sleep_time)

    log_message(f"{market_type.value} scanner stopped", level="WARN")


def start_scanner_thread(market_type: MarketType, sleep_time: int = 10) -> dict:
    """
    Starts a scanner in a separate thread.

    Returns:
        dict with 'thread' and 'stop_event' for external control
    """
    if market_type.value in active_scanners:
        return {
            "status": "already_running",
            "message": f"{market_type.value} scanner is already running",
        }

    stop_event = threading.Event()
    thread = threading.Thread(
        target=execute_market_scanner,
        args=(market_type, sleep_time, stop_event),
        daemon=True,
        name=f"Scanner-{market_type.value}",
    )
    thread.start()

    # Guardar referencias
    active_scanners[market_type.value] = thread
    stop_events[market_type.value] = stop_event

    return {"status": "started", "thread": thread, "stop_event": stop_event}


def stop_scanner(market_type: MarketType) -> dict:
    """
    Stops a specific scanner.

    Returns:
        dict with the operation status
    """
    market_name = market_type.value

    if market_name not in active_scanners:
        return {
            "status": "not_running",
            "message": f"{market_name} scanner is not running",
        }

    stop_event = stop_events[market_name]
    stop_event.set()

    # Esperar a que termine (máximo 5 segundos)
    thread = active_scanners[market_name]
    thread.join(timeout=5)

    # Limpiar referencias
    del active_scanners[market_name]
    del stop_events[market_name]

    return {
        "status": "stopped",
        "message": f"{market_name} scanner stopped successfully",
    }


def stop_all_scanners():
    """Stops all active scanners"""
    log_message("Stopping all scanners...", level="WARN")

    for market_name in list(active_scanners.keys()):
        market_type = MarketType(market_name)
        stop_scanner(market_type)

    log_message("All scanners stopped")


def get_scanner_status() -> dict:
    """
    Returns status of all scanners.

    Returns:
        dict with the status of each scanner
    """
    return {
        market: {"running": True, "thread_alive": thread.is_alive()}
        for market, thread in active_scanners.items()
    }
