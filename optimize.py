import sqlite3
import os

DB_PATH = "ExcelDB.db"

def optimize_pragma(conn):
    """Apply maximum SQLite compression settings."""
    conn.execute("PRAGMA page_size = 4096")  # 4KB pages often give best compression
    conn.execute("PRAGMA auto_vacuum = INCREMENTAL")  # Uses minimal reserved space
    conn.execute("PRAGMA journal_mode = DELETE")  # Removes WAL logs permanently
    conn.execute("PRAGMA synchronous = NORMAL")  # Speeds up vacuuming

def remove_unused_indexes(conn):
    """Removes non-primary key indexes to reduce size safely."""
    cursor = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='index' 
        AND sql IS NOT NULL
    """)
    indexes = cursor.fetchall()

    for index in indexes:
        index_name = index[0]
        print(f"Dropping non-essential index: {index_name}")
        conn.execute(f"DROP INDEX IF EXISTS {index_name}")

def vacuum_database(conn):
    """Defragments and fully compresses the database."""
    conn.execute("PRAGMA incremental_vacuum(1000)")  # Frees up extra space
    conn.execute("VACUUM")  # Fully compacts the database

def rebuild_database():
    """Applies all optimizations directly to ExcelDB.db."""
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found!")
        return

    conn = sqlite3.connect(DB_PATH)

    print("Applying PRAGMA optimizations...")
    optimize_pragma(conn)

    print("Vacuuming database for compression...")
    vacuum_database(conn)

    conn.commit()
    conn.close()
    print("Optimization complete!")

if __name__ == "__main__":
    rebuild_database()
