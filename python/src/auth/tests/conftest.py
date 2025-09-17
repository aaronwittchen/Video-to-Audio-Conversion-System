import os
import sys
import pytest
import sqlite3
from contextlib import contextmanager
from flask import Flask
import server
from server import server as flask_app

# Add the src/auth folder to Python path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Global SQLite connection
_conn = None

def get_sqlite_connection():
    """Get or create a SQLite in-memory database connection."""
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(":memory:", check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        
        with _conn:
            _conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    verification_token TEXT,
                    verified BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
    return _conn

class MockMySQLCursor:
    """Mock MySQL cursor that uses SQLite underneath."""
    
    def __init__(self, sqlite_conn):
        self.sqlite_conn = sqlite_conn
        self._cursor = sqlite_conn.cursor()
        
    def execute(self, query, params=None):
        """Execute a query, converting MySQL syntax to SQLite where needed."""
        # Convert MySQL %s placeholders to SQLite ? placeholders
        sqlite_query = query.replace('%s', '?')
        # Convert MySQL NOW() to SQLite datetime('now')
        sqlite_query = sqlite_query.replace("NOW()", "datetime('now')")
        
        if params:
            result = self._cursor.execute(sqlite_query, params)
        else:
            result = self._cursor.execute(sqlite_query)
        
        # Return the number of affected rows (for MySQL compatibility)
        return self._cursor.rowcount
    
    def fetchone(self):
        """Fetch one row."""
        row = self._cursor.fetchone()
        if row is None:
            return None
        # Convert sqlite3.Row to tuple for MySQL compatibility
        return tuple(row)
    
    def fetchall(self):
        """Fetch all rows."""
        return [tuple(row) for row in self._cursor.fetchall()]
    
    def close(self):
        """Close the cursor."""
        self._cursor.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

class MockMySQLConnection:
    """Mock MySQL connection that uses SQLite."""
    
    def __init__(self, sqlite_conn):
        self.sqlite_conn = sqlite_conn
    
    def cursor(self):
        """Create a new cursor."""
        return MockMySQLCursor(self.sqlite_conn)
    
    def commit(self):
        """Commit the current transaction."""
        self.sqlite_conn.commit()
    
    def rollback(self):
        """Rollback the current transaction."""
        self.sqlite_conn.rollback()

class MockMySQL:
    def __init__(self, app):
        self._sqlite_conn = get_sqlite_connection()
        self.connection = MockMySQLConnection(self._sqlite_conn)
        self.connected = True

# Override the get_mysql function in the server module
def get_mysql():
    return MockMySQL(None)

# Replace the original get_mysql with our test version
server.get_mysql = get_mysql

@pytest.fixture(scope="session")
def app():
    """Create and configure a new app instance for each test."""
    # Set testing environment variables
    os.environ["TESTING"] = "true"
    os.environ["JWT_SECRET"] = "testsecret"
    
    # Configure Flask app for testing
    flask_app.config['TESTING'] = True
    
    yield flask_app
    
    # Clean up after tests
    global _conn
    if _conn:
        _conn.close()
        _conn = None

@pytest.fixture()
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture(autouse=True)
def clear_users_table():
    """Clear the users table before each test."""
    conn = get_sqlite_connection()
    with conn:
        conn.execute("DELETE FROM users")
        conn.commit()