"""
Configuration Management Module
================================================================================
Centralized configuration for the Stock Market Scanner application.

This module handles all application configuration including:
- Database connection parameters
- API credentials
- Application settings
- Environment-specific configurations

Usage:
    from config import config

    # Access configuration values
    db_host = config.db_host

    # Validate configuration on startup
    config.validate()
================================================================================
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def load_env_file():
    """Load environment variables from .env file if it exists"""
    try:
        from dotenv import \
            load_dotenv  # pylint: disable=import-outside-toplevel

        env_path = Path(__file__).parent / ".env"
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
            return True
        return False
    except ImportError:
        # python-dotenv not installed, skip .env file loading
        return False


# Load .env file if available
load_env_file()


@dataclass
class DatabaseConfig:
    """Database connection configuration"""

    host: str = field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("DB_PORT", "5432")))
    name: str = field(default_factory=lambda: os.getenv("DB_NAME", "trading"))
    user: str = field(default_factory=lambda: os.getenv("DB_USER", "postgres"))
    password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", ""))

    # Connection pool settings
    min_connections: int = field(
        default_factory=lambda: int(os.getenv("DB_MIN_CONN", "5"))
    )
    max_connections: int = field(
        default_factory=lambda: int(os.getenv("DB_MAX_CONN", "20"))
    )

    def validate(self) -> list[str]:
        """
        Validate database configuration

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not self.host:
            errors.append("DB_HOST is required")

        if not self.name:
            errors.append("DB_NAME is required")

        if not self.user:
            errors.append("DB_USER is required")

        if self.port < 1 or self.port > 65535:
            errors.append(f"DB_PORT must be between 1-65535, got: {self.port}")

        if self.min_connections < 1:
            errors.append(f"DB_MIN_CONN must be >= 1, got: {self.min_connections}")

        if self.max_connections < self.min_connections:
            errors.append(
                f"DB_MAX_CONN ({self.max_connections}) "
                f"must be >= DB_MIN_CONN ({self.min_connections})"
            )

        return errors

    def get_connection_string(self) -> str:
        """
        Generate PostgreSQL connection string

        Returns:
            Connection string for psycopg2
        """
        return (
            f"host={self.host} "
            f"port={self.port} "
            f"dbname={self.name} "
            f"user={self.user} "
            f"password={self.password}"
        )


@dataclass
class SchwabAPIConfig:
    """Charles Schwab API configuration"""

    app_key: Optional[str] = field(default_factory=lambda: os.getenv("APP_KEY_SCHWAB"))
    client_secret: Optional[str] = field(
        default_factory=lambda: os.getenv("CLIENT_SECRET_SCHWAB")
    )

    def validate(self) -> list[str]:
        """
        Validate Schwab API configuration

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not self.app_key:
            errors.append(
                "APP_KEY_SCHWAB is required (get from https://developer.schwab.com/)"
            )

        if not self.client_secret:
            errors.append("CLIENT_SECRET_SCHWAB is required")

        return errors


@dataclass
class OptionalAPIConfig:
    """Optional third-party API configurations"""

    alpha_vantage_key: Optional[str] = field(
        default_factory=lambda: os.getenv("ALPHA_VANTAGE_API_KEY")
    )
    polygon_key: Optional[str] = field(
        default_factory=lambda: os.getenv("POLYGON_API_KEY")
    )
    fmp_key: Optional[str] = field(default_factory=lambda: os.getenv("FMP_API_KEY"))
    alpaca_client_id: Optional[str] = field(
        default_factory=lambda: os.getenv("ALPACA_CLIENT_ID")
    )
    alpaca_client_secret: Optional[str] = field(
        default_factory=lambda: os.getenv("ALPACA_CLIENT_SECRET")
    )
    intrinio_key: Optional[str] = field(
        default_factory=lambda: os.getenv("INTRINIO_API_KEY")
    )

    def get_configured_apis(self) -> list[str]:
        """
        Get list of configured optional APIs

        Returns:
            List of API names that have credentials configured
        """
        configured = []

        if self.alpha_vantage_key:
            configured.append("Alpha Vantage")
        if self.polygon_key:
            configured.append("Polygon.io")
        if self.fmp_key:
            configured.append("Financial Modeling Prep")
        if self.alpaca_client_id and self.alpaca_client_secret:
            configured.append("Alpaca Markets")
        if self.intrinio_key:
            configured.append("Intrinio")

        return configured


@dataclass
class ApplicationConfig:
    """Application-level configuration"""

    # Scanner settings
    sleep_time: int = field(
        default_factory=lambda: int(os.getenv("SCANNER_SLEEP_TIME", "10"))
    )
    output_length: int = field(
        default_factory=lambda: int(os.getenv("SCANNER_OUTPUT_LENGTH", "15"))
    )

    # Logging settings
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    log_format: str = field(
        default_factory=lambda: os.getenv("LOG_FORMAT", "text")  # 'text' or 'json'
    )

    # Environment
    environment: str = field(
        default_factory=lambda: os.getenv("ENVIRONMENT", "development")
    )

    def validate(self) -> list[str]:
        """
        Validate application configuration

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if self.sleep_time < 1:
            errors.append(
                f"SCANNER_SLEEP_TIME must be >= 1 second, got: {self.sleep_time}"
            )

        if self.sleep_time < 10:
            errors.append(
                f"WARNING: SCANNER_SLEEP_TIME is {self.sleep_time} seconds. "
                f"Values < 10 may violate rate limits or Terms of Service."
            )

        if self.output_length < 1:
            errors.append(
                f"SCANNER_OUTPUT_LENGTH must be >= 1, got: {self.output_length}"
            )

        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            errors.append(
                f"LOG_LEVEL must be one of {valid_log_levels}, got: {self.log_level}"
            )

        valid_log_formats = ["text", "json"]
        if self.log_format not in valid_log_formats:
            errors.append(
                f"LOG_FORMAT must be one of {valid_log_formats}, got: {self.log_format}"
            )

        valid_environments = ["development", "testing", "production"]
        if self.environment not in valid_environments:
            errors.append(
                f"ENVIRONMENT must be one of {valid_environments}, got: {self.environment}"
            )

        return errors

    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == "development"


@dataclass
class Config:
    """
    Master configuration class

    Aggregates all configuration sections and provides validation.
    """

    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    schwab_api: SchwabAPIConfig = field(default_factory=SchwabAPIConfig)
    optional_apis: OptionalAPIConfig = field(default_factory=OptionalAPIConfig)
    app: ApplicationConfig = field(default_factory=ApplicationConfig)

    def validate(self, require_schwab: bool = True) -> None:
        """
        Validate entire configuration

        Args:
            require_schwab: If True, Schwab API credentials are required

        Raises:
            ValueError: If configuration is invalid
        """
        all_errors = []

        # Validate each section
        all_errors.extend(self.database.validate())

        if require_schwab:
            all_errors.extend(self.schwab_api.validate())

        all_errors.extend(self.app.validate())

        # Raise if any errors found
        if all_errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(
                f"  - {err}" for err in all_errors
            )
            raise ValueError(error_msg)

    def print_summary(self) -> None:
        """Print configuration summary (safe for logging)"""
        print("=" * 80)
        print("Configuration Summary")
        print("=" * 80)

        print("\nDatabase:")
        print(f"  Host: {self.database.host}:{self.database.port}")
        print(f"  Database: {self.database.name}")
        print(f"  User: {self.database.user}")
        print(
            f"  Password: {'*' * len(self.database.password) \
                             if self.database.password else '(not set)'}"
        )
        print(
            f"  Connection Pool: {self.database.min_connections}-{self.database.max_connections}"
        )

        print("\nSchwab API:")
        print(f"  App Key: {'*' * 20 if self.schwab_api.app_key else '(not set)'}")
        print(
            f"  Client Secret: {'*' * 20 if self.schwab_api.client_secret else '(not set)'}"
        )

        configured_apis = self.optional_apis.get_configured_apis()
        print("\nOptional APIs:")
        if configured_apis:
            for api in configured_apis:
                print(f"  ✓ {api}")
        else:
            print("  (none configured)")

        print("\nApplication:")
        print(f"  Environment: {self.app.environment}")
        print(f"  Sleep Time: {self.app.sleep_time} seconds")
        print(f"  Output Length: {self.app.output_length}")
        print(f"  Log Level: {self.app.log_level}")
        print(f"  Log Format: {self.app.log_format}")

        print("=" * 80)


# Global configuration instance
config = Config()


# Convenience functions
def validate_config(require_schwab: bool = True) -> None:
    """
    Validate configuration and raise if invalid

    Args:
        require_schwab: If True, Schwab API credentials are required

    Raises:
        ValueError: If configuration is invalid
    """
    config.validate(require_schwab=require_schwab)


def get_config() -> Config:
    """
    Get the global configuration instance

    Returns:
        Config instance
    """
    return config


if __name__ == "__main__":
    # Test configuration when run directly
    try:
        print("Testing configuration...")
        config.validate(require_schwab=False)
        config.print_summary()
        print("\n✓ Configuration is valid!")
    except ValueError as e:
        print(f"\n✗ Configuration errors:\n{e}")
