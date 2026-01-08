"""
Database layer for crypto data storage using SQLite.
"""
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import pandas as pd

DB_PATH = Path(__file__).parent / "data" / "crypto_data.db"


def get_connection():
    """Get a database connection."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database with required tables."""
    conn = get_connection()
    cursor = conn.cursor()

    # Crypto prices table (from CoinGecko)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            coin_id TEXT NOT NULL,
            symbol TEXT,
            name TEXT,
            timestamp INTEGER NOT NULL,
            price_usd REAL,
            market_cap REAL,
            volume_24h REAL,
            UNIQUE(coin_id, timestamp)
        )
    """)

    # DeFi TVL data (from DeFiLlama)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tvl (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            protocol_id TEXT NOT NULL,
            protocol_name TEXT,
            chain TEXT,
            timestamp INTEGER NOT NULL,
            tvl_usd REAL,
            UNIQUE(protocol_id, timestamp)
        )
    """)

    # Chain TVL data
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chain_tvl (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chain TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            tvl_usd REAL,
            UNIQUE(chain, timestamp)
        )
    """)

    # Metadata for tracking what we've fetched
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fetch_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_type TEXT NOT NULL,
            identifier TEXT NOT NULL,
            last_fetched INTEGER,
            UNIQUE(data_type, identifier)
        )
    """)

    # Create indexes for faster queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prices_coin_timestamp ON prices(coin_id, timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tvl_protocol_timestamp ON tvl(protocol_id, timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chain_tvl_timestamp ON chain_tvl(chain, timestamp)")

    conn.commit()
    conn.close()


def save_prices(coin_id: str, symbol: str, name: str, prices_data: list):
    """
    Save price data for a coin.
    prices_data: list of [timestamp_ms, price] pairs
    """
    conn = get_connection()
    cursor = conn.cursor()

    for timestamp_ms, price in prices_data:
        timestamp = int(timestamp_ms / 1000)  # Convert to seconds
        cursor.execute("""
            INSERT OR REPLACE INTO prices (coin_id, symbol, name, timestamp, price_usd)
            VALUES (?, ?, ?, ?, ?)
        """, (coin_id, symbol, name, timestamp, price))

    # Update fetch metadata
    cursor.execute("""
        INSERT OR REPLACE INTO fetch_metadata (data_type, identifier, last_fetched)
        VALUES ('price', ?, ?)
    """, (coin_id, int(datetime.now().timestamp())))

    conn.commit()
    conn.close()


def save_tvl(protocol_id: str, protocol_name: str, tvl_data: list, chain: str = None):
    """
    Save TVL data for a protocol.
    tvl_data: list of {"date": timestamp, "totalLiquidityUSD": value} dicts
    """
    conn = get_connection()
    cursor = conn.cursor()

    for entry in tvl_data:
        timestamp = int(entry.get("date", 0))
        tvl = entry.get("totalLiquidityUSD", 0)
        cursor.execute("""
            INSERT OR REPLACE INTO tvl (protocol_id, protocol_name, chain, timestamp, tvl_usd)
            VALUES (?, ?, ?, ?, ?)
        """, (protocol_id, protocol_name, chain, timestamp, tvl))

    cursor.execute("""
        INSERT OR REPLACE INTO fetch_metadata (data_type, identifier, last_fetched)
        VALUES ('tvl', ?, ?)
    """, (protocol_id, int(datetime.now().timestamp())))

    conn.commit()
    conn.close()


def save_chain_tvl(chain: str, tvl_data: list):
    """
    Save TVL data for a chain.
    tvl_data: list of {"date": timestamp, "tvl": value} dicts
    """
    conn = get_connection()
    cursor = conn.cursor()

    for entry in tvl_data:
        timestamp = int(entry.get("date", 0))
        tvl = entry.get("tvl", 0)
        cursor.execute("""
            INSERT OR REPLACE INTO chain_tvl (chain, timestamp, tvl_usd)
            VALUES (?, ?, ?)
        """, (chain, timestamp, tvl))

    cursor.execute("""
        INSERT OR REPLACE INTO fetch_metadata (data_type, identifier, last_fetched)
        VALUES ('chain_tvl', ?, ?)
    """, (chain, int(datetime.now().timestamp())))

    conn.commit()
    conn.close()


def get_prices(coin_id: str, start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
    """Get price data for a coin as a DataFrame."""
    conn = get_connection()

    query = "SELECT * FROM prices WHERE coin_id = ?"
    params = [coin_id]

    if start_date:
        query += " AND timestamp >= ?"
        params.append(int(start_date.timestamp()))
    if end_date:
        query += " AND timestamp <= ?"
        params.append(int(end_date.timestamp()))

    query += " ORDER BY timestamp"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    if not df.empty:
        df['date'] = pd.to_datetime(df['timestamp'], unit='s')

    return df


def get_tvl(protocol_id: str, start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
    """Get TVL data for a protocol as a DataFrame."""
    conn = get_connection()

    query = "SELECT * FROM tvl WHERE protocol_id = ?"
    params = [protocol_id]

    if start_date:
        query += " AND timestamp >= ?"
        params.append(int(start_date.timestamp()))
    if end_date:
        query += " AND timestamp <= ?"
        params.append(int(end_date.timestamp()))

    query += " ORDER BY timestamp"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    if not df.empty:
        df['date'] = pd.to_datetime(df['timestamp'], unit='s')

    return df


def get_chain_tvl(chain: str, start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
    """Get TVL data for a chain as a DataFrame."""
    conn = get_connection()

    query = "SELECT * FROM chain_tvl WHERE chain = ?"
    params = [chain]

    if start_date:
        query += " AND timestamp >= ?"
        params.append(int(start_date.timestamp()))
    if end_date:
        query += " AND timestamp <= ?"
        params.append(int(end_date.timestamp()))

    query += " ORDER BY timestamp"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    if not df.empty:
        df['date'] = pd.to_datetime(df['timestamp'], unit='s')

    return df


def get_available_coins() -> list:
    """Get list of coins we have data for."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT coin_id, symbol, name FROM prices")
    results = cursor.fetchall()
    conn.close()
    return [{"coin_id": r["coin_id"], "symbol": r["symbol"], "name": r["name"]} for r in results]


def get_available_protocols() -> list:
    """Get list of protocols we have TVL data for."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT protocol_id, protocol_name FROM tvl")
    results = cursor.fetchall()
    conn.close()
    return [{"protocol_id": r["protocol_id"], "name": r["protocol_name"]} for r in results]


def get_available_chains() -> list:
    """Get list of chains we have TVL data for."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT chain FROM chain_tvl")
    results = cursor.fetchall()
    conn.close()
    return [r["chain"] for r in results]


def needs_refresh(data_type: str, identifier: str, max_age_hours: int = 24) -> bool:
    """Check if data needs to be refreshed."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT last_fetched FROM fetch_metadata
        WHERE data_type = ? AND identifier = ?
    """, (data_type, identifier))
    result = cursor.fetchone()
    conn.close()

    if not result:
        return True

    last_fetched = datetime.fromtimestamp(result["last_fetched"])
    return datetime.now() - last_fetched > timedelta(hours=max_age_hours)


# Initialize database on import
init_db()
