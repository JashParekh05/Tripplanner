"""
Database operations for flight price tracking
"""
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class FlightDatabase:
    """Manages flight price data storage"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def _init_database(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Flight prices table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS flight_prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    origin TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    departure_date TEXT NOT NULL,
                    return_date TEXT,
                    price REAL NOT NULL,
                    currency TEXT NOT NULL,
                    airline TEXT,
                    stops INTEGER,
                    flight_url TEXT,
                    is_multi_leg BOOLEAN DEFAULT 0,
                    leg_details TEXT,
                    data_source TEXT DEFAULT 'serpapi',
                    found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notified BOOLEAN DEFAULT 0
                )
            ''')

            # Add data_source column to existing tables if it doesn't exist
            try:
                cursor.execute('ALTER TABLE flight_prices ADD COLUMN data_source TEXT DEFAULT "serpapi"')
            except sqlite3.OperationalError:
                pass  # Column already exists

            # Price history for trend analysis
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    route_key TEXT NOT NULL,
                    price REAL NOT NULL,
                    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Alerts sent
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts_sent (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    flight_id INTEGER,
                    alert_type TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (flight_id) REFERENCES flight_prices(id)
                )
            ''')

            # Create indices for better query performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_prices_route
                ON flight_prices(origin, destination, departure_date)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_prices_price
                ON flight_prices(price)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_history_route
                ON price_history(route_key, checked_at)
            ''')

            conn.commit()
            logger.info("Database initialized successfully")

    def save_flight_price(self, flight_data: Dict) -> int:
        """Save flight price data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO flight_prices
                (origin, destination, departure_date, return_date, price, currency,
                 airline, stops, flight_url, is_multi_leg, leg_details, data_source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                flight_data['origin'],
                flight_data['destination'],
                flight_data['departure_date'],
                flight_data.get('return_date'),
                flight_data['price'],
                flight_data['currency'],
                flight_data.get('airline'),
                flight_data.get('stops', 0),
                flight_data.get('url'),
                flight_data.get('is_multi_leg', False),
                flight_data.get('leg_details'),
                flight_data.get('data_source', 'serpapi')
            ))

            flight_id = cursor.lastrowid

            # Also save to price history
            route_key = f"{flight_data['origin']}-{flight_data['destination']}-{flight_data['departure_date']}"
            cursor.execute('''
                INSERT INTO price_history (route_key, price)
                VALUES (?, ?)
            ''', (route_key, flight_data['price']))

            logger.info(f"Saved flight price: {route_key} @ ${flight_data['price']}")
            return flight_id

    def get_lowest_price(self, origin: str, destination: str, departure_date: str) -> Optional[float]:
        """Get the lowest recorded price for a route"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT MIN(price) as min_price
                FROM flight_prices
                WHERE origin = ? AND destination = ? AND departure_date = ?
            ''', (origin, destination, departure_date))

            result = cursor.fetchone()
            return result['min_price'] if result['min_price'] else None

    def get_recent_deals(self, max_price: float, limit: int = 10) -> List[Dict]:
        """Get recent flight deals below max price"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM flight_prices
                WHERE price <= ?
                ORDER BY found_at DESC
                LIMIT ?
            ''', (max_price, limit))

            return [dict(row) for row in cursor.fetchall()]

    def get_unnotified_deals(self, max_price: float) -> List[Dict]:
        """Get deals that haven't been notified yet"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM flight_prices
                WHERE price <= ? AND notified = 0
                ORDER BY price ASC
            ''', (max_price,))

            return [dict(row) for row in cursor.fetchall()]

    def mark_as_notified(self, flight_id: int, alert_type: str = 'email'):
        """Mark a flight as notified"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE flight_prices
                SET notified = 1
                WHERE id = ?
            ''', (flight_id,))

            cursor.execute('''
                INSERT INTO alerts_sent (flight_id, alert_type)
                VALUES (?, ?)
            ''', (flight_id, alert_type))

            logger.info(f"Marked flight {flight_id} as notified")

    def get_price_trend(self, origin: str, destination: str, days: int = 7) -> List[Dict]:
        """Get price trend for a route over the last N days"""
        route_key = f"{origin}-{destination}-%"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT route_key, price, checked_at
                FROM price_history
                WHERE route_key LIKE ?
                AND datetime(checked_at) >= datetime('now', '-' || ? || ' days')
                ORDER BY checked_at ASC
            ''', (route_key, days))

            return [dict(row) for row in cursor.fetchall()]

    def cleanup_old_data(self, days: int = 30):
        """Remove old flight data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM flight_prices
                WHERE datetime(found_at) < datetime('now', '-' || ? || ' days')
            ''', (days,))

            deleted = cursor.rowcount
            logger.info(f"Cleaned up {deleted} old flight records")
            return deleted
