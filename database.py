"""
Database access and schema management for E-Commerce Sales & Customer Analytics.
Uses SQLite for zero-setup, high-performance local relational storage.
"""

import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ecommerce.db")

def get_db_connection():
    """Returns a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

@contextmanager
def get_db():
    """Context manager for SQLite connections with automatic commit/rollback."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Initializes SQLite database tables and performance indexes."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Customers Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                city TEXT,
                country TEXT DEFAULT 'United States',
                segment TEXT DEFAULT 'Standard',
                signup_date TIMESTAMP NOT NULL
            );
        """)
        
        # Products Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                cost_price REAL NOT NULL,
                retail_price REAL NOT NULL,
                stock_quantity INTEGER NOT NULL DEFAULT 100
            );
        """)
        
        # Orders Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                order_date TIMESTAMP NOT NULL,
                status TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                shipping_cost REAL DEFAULT 0.0,
                total_amount REAL NOT NULL,
                total_profit REAL NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            );
        """)
        
        # Order Items Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                unit_cost REAL NOT NULL,
                total_price REAL NOT NULL,
                total_profit REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id)
            );
        """)
        
        # Performance Indexes for fast analytical queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_order ON order_items(order_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_product ON order_items(product_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);")

def check_db_seeded() -> bool:
    """Checks if the database already contains seeded data."""
    if not os.path.exists(DB_PATH):
        return False
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM orders")
            count = cursor.fetchone()[0]
            return count > 1000
    except Exception:
        return False

if __name__ == "__main__":
    init_db()
    print(f"Database initialized successfully at {DB_PATH}")
