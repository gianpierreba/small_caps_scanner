"""
Database operations using connection pooling with psycopg2.
This module provides classes to handle database connections and operations
efficiently using a threaded connection pool.
"""

import atexit
import os
import sys
from typing import Optional
from psycopg2 import DatabaseError, OperationalError
from psycopg2.pool import ThreadedConnectionPool

# Import centralized configuration
try:
    from config import config
except ImportError:
    # Fallback if config module not available
    config = None


class DatabaseConnection:
    """
    Manages a threaded connection pool for PostgreSQL database connections.
    """

    # Class-level variable for the connection pool
    connection_pool = None

    @classmethod
    def initialize_pool(
        cls,
        minconn,
        maxconn,
        **db_params
    ):
        """
        Initialize the connection pool.
        This should be called once, typically when the application starts.
        """
        if cls.connection_pool is None:
            cls.connection_pool = ThreadedConnectionPool(
                minconn=minconn,
                maxconn=maxconn,
                **db_params
            )

    @classmethod
    def close_pool(cls):
        """
        Close all connections in the pool.
        Preferred to be called when the application is shutting down.
        """
        if cls.connection_pool is not None:
            cls.connection_pool.closeall()

    @classmethod
    def get_connection(cls):
        """
        Get a connection from the pool.
        """
        if cls.connection_pool is None:
            raise ConnectionError("Connection pool is not initialized.")
        return cls.connection_pool.getconn()

    @classmethod
    def release_connection(
        cls,
        connection
    ):
        """
        Return a connection to the pool.

        Parameters:
        - connection: The connection object to be returned to the pool.

        returns: None
        """
        if cls.connection_pool is not None:
            cls.connection_pool.putconn(connection)


class DatabaseOperation:
    """
    Base class for database operations.
    Provides methods to open and close connections using the connection pool.
    """

    def __init__(self):
        """
        Initialize the DatabaseOperation with no active connection or cursor.
        """
        self.conn = None
        self.cursor = None

    def open_connection(self):
        """
        Acquire a connection from the pool and initialize a cursor.
        """
        self.conn = DatabaseConnection.get_connection()
        self.cursor = self.conn.cursor()

    def close_connection(self):
        """
        Close the cursor and release the connection back to the pool.
        """
        if self.cursor:
            self.cursor.close()
        if self.conn:
            DatabaseConnection.release_connection(
                self.conn
            )


class InsertData(DatabaseOperation):
    """Insert data into DB"""
    def insert_data(
            self,
            table: str,
            data: dict
        ):
        """
        Insert data into the specified table.

        Parameters:
        - table: Name of the table to insert data into.
        - data: A dictionary where keys are column names and values are the values to be inserted.

        Returns: None

        Example:
        insert_data("users", {"name": "Alice", "age": 30})
        """
        try:
            self.open_connection()
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["%s"] * len(data))
            insert_query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            values_to_insert = list(data.values())
            self.cursor.execute(insert_query, values_to_insert)
            self.conn.commit()
        except (OperationalError, DatabaseError) as e:
            print(f"Error: {e}")
            self.conn.rollback()
        finally:
            self.close_connection()


class RetrieveData(DatabaseOperation):
    """
    Retrieve data from the database.
    """
    # pylint: disable=too-many-positional-arguments,too-many-arguments
    def retrieve_data(
            self,
            table_name: str,
            condition_column: Optional[str] = None,
            condition_value: Optional[str] = None,
            column: Optional[str] = None,
            fetch_all: Optional[bool] = True
        ) -> list:
        """
        Retrieve data from a table with an optional WHERE clause using parameterized queries.

        Parameters:
        - table_name (str): Name of the table to query.
        - condition_column (str): Column name for the WHERE clause (optional).
        - condition_value (str): Value for the WHERE clause (optional).
        - column (str): Specific column to retrieve (optional, defaults to all columns).
        - fetch_all (bool): If True, fetch all results; otherwise, fetch one. Defaults to True.

        Returns:
            list: List of results if fetch_all is True; otherwise, a single result.

        Example:
        - Retrieves the name of the user with id 123:
            data = retrieve_data(
            "users",
            condition_column="id",
            condition_value="123",
            column="name",
            fetch_all=False
        )
        """
        try:
            self.open_connection()
            column = column or '*'
            query = f"SELECT {column} FROM {table_name}"
            if condition_column and condition_value:
                query += f" WHERE {condition_column} = %s"
                self.cursor.execute(query, (condition_value,))
            else:
                self.cursor.execute(query)
            if fetch_all:
                return self.cursor.fetchall()
            return self.cursor.fetchone()
        except (OperationalError, DatabaseError) as e:
            print(f"Error: {e}")
            return []
        finally:
            self.close_connection()

    def execute_custom_query(
            self,
            query: str,
            params: tuple = (),
            retrieve: bool = True,
            fetch_all: bool = True
        ) -> list:
        """
        Execute a custom SQL query.

        Parameters:
            query (str): The SQL query string with placeholders for parameters.
            params (tuple): A tuple containing the parameters to be passed to the query.
            fetch_all (bool): If True, fetch all results; otherwise, fetch one.

        Returns:
            list: List of results if fetch_all is True; otherwise, a single result.

        Example:
        - Retrieves names of users older than 25
            results = execute_custom_query(
                "SELECT name FROM users WHERE age > %s",
                (25,),
                retrieve=True,
                fetch_all=True
            )
        """
        try:
            self.open_connection()
            if retrieve:
                self.cursor.execute(query, params)
                if fetch_all:
                    return self.cursor.fetchall()
                return self.cursor.fetchone()
            self.cursor.execute(query, params)
            self.conn.commit()
        except (OperationalError, DatabaseError) as e:
            print(f"Error executing custom query: {e}")
            if not retrieve:
                self.conn.rollback()
            return []
        finally:
            self.close_connection()
        return []


class UpdateData(DatabaseOperation):
    """Update data in DB"""
    def update_data(
            self,
            table: str,
            update_data: dict,
            where_constraint_column: str,
            where_constraint_data: str
        ):
        """
        Update data in the specified table.

        Parameters:
        - table (str): Name of the table to update.
        - update_data (dict): A dictionary where keys are column names
            to be updated, and values are the new values.
        - where_constraint_column (str): The column used in the WHERE clause
            for the update condition.
        - where_constraint_data (str): The value used in the WHERE clause
            for the update condition.

        Returns: None

        Example:
        - Updates Alice's age to 31
            update_data("users", {"age": 31}, "name", "Alice")
        """
        try:
            self.open_connection()
            set_clause = ", ".join(
                [f"{key} = %s" for key in update_data.keys()])
            update_query = f"UPDATE {table} SET {set_clause} WHERE {where_constraint_column} = %s"
            data_to_update = list(update_data.values()) + \
                [where_constraint_data]
            self.cursor.execute(update_query, data_to_update)
            self.conn.commit()
        except (OperationalError, DatabaseError) as e:
            print(f"Error: {e}")
            self.conn.rollback()
        finally:
            self.close_connection()


# Initialize the connection pool using centralized configuration
if config is not None:
    # Use config module (recommended)
    db_config = config.database
    DatabaseConnection.initialize_pool(
        minconn=db_config.min_connections,
        maxconn=db_config.max_connections,
        host=db_config.host,
        port=db_config.port,
        database=db_config.name,
        user=db_config.user,
        password=db_config.password
    )
else:
    # Fallback to environment variables only (legacy support)
    DatabaseConnection.initialize_pool(
        minconn=int(os.getenv('DB_MIN_CONN', '5')),
        maxconn=int(os.getenv('DB_MAX_CONN', '20')),
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', '5432')),
        database=os.getenv('DB_NAME', 'trading'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', '')
    )

# Cleanup when the application stops
atexit.register(DatabaseConnection.close_pool)

if __name__ == "__main__":
    # Test connection pool and database operations when running directly.
    # Usage: python scanners_db.py
    print("=" * 60)
    print("Testing Database Connection Pool")
    print("=" * 60)

    try:
        # Test 1: Check if connection pool is initialized
        print("\n[Test 1] Checking if connection pool is initialized...")
        if DatabaseConnection.connection_pool is not None:
            print("✓ Connection pool initialized successfully")
        else:
            print("✗ Connection pool is NOT initialized")
            sys.exit(0)

        # Test 2: Get a connection from the pool
        print("\n[Test 2] Getting a connection from the pool...")
        conn = DatabaseConnection.get_connection()
        print("✓ Successfully acquired a connection")

        # Test 3: Test the connection with a simple query
        print("\n[Test 3] Testing connection with a simple query...")
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"✓ Query executed successfully. Result: {result}")
        cursor.close()

        # Test 4: Release the connection back to the pool
        print("\n[Test 4] Releasing connection back to the pool...")
        DatabaseConnection.release_connection(conn)
        print("✓ Connection released successfully")

        # Test 5: Test RetrieveData class
        print("\n[Test 5] Testing RetrieveData class...")
        retriever = RetrieveData()
        try:
            # This will fail if the table doesn't exist,
            # but that's okay - we're just testing the connection
            retriever.open_connection()
            print("✓ RetrieveData connection opened successfully")
            retriever.close_connection()
            print("✓ RetrieveData connection closed successfully")
        except (OperationalError, DatabaseError) as e:
            print(f"⚠  RetrieveData test encountered an issue: {e}")

        # Test 6: Multiple connections from pool
        print("\n[Test 6] Testing multiple connections from pool...")
        connections = []
        NUM_CONNECTIONS = 3
        for i in range(NUM_CONNECTIONS):
            conn = DatabaseConnection.get_connection()
            connections.append(conn)
            print(f"  ✓ Got connection {i + 1}/{NUM_CONNECTIONS}")

        for i, conn in enumerate(connections):
            DatabaseConnection.release_connection(conn)
            print(f"  ✓ Released connection {i + 1}/{NUM_CONNECTIONS}")

        print("\n" + "=" * 60)
        print("✓ All connection tests passed!")
        print("=" * 60)

    except (OperationalError, DatabaseError) as e:
        print(f"\n✗ Error during testing: {e}")
        print("=" * 60)
        sys.exit(0)
