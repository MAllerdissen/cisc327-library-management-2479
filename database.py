"""
Database module for Library Management System
Handles all database operations and connections
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Database configuration
DATABASE = 'library.db'

def get_db_connection():
    """Get a database connection with row factory returning dict-like rows."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# ---------- Initialization & Sample Data ----------

def init_database() -> None:
    """Create tables if they do not already exist."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS books ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "title TEXT NOT NULL,"
        "author TEXT NOT NULL,"
        "isbn TEXT UNIQUE NOT NULL,"
        "total_copies INTEGER NOT NULL,"
        "available_copies INTEGER NOT NULL)"
    )
    cur.execute(
        "CREATE TABLE IF NOT EXISTS borrow_records ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "patron_id TEXT NOT NULL,"
        "book_id INTEGER NOT NULL,"
        "borrow_date TEXT NOT NULL,"
        "due_date TEXT NOT NULL,"
        "return_date TEXT NULL,"
        "FOREIGN KEY (book_id) REFERENCES books (id))"
    )
    conn.commit()
    conn.close()

def add_sample_data() -> None:
    """Insert a few books if catalog is empty (for demo/testing)."""
    conn = get_db_connection()
    cur = conn.cursor()
    count = cur.execute('SELECT COUNT(*) FROM books').fetchone()[0]
    if count == 0:
        sample = [
            ('The Great Gatsby', 'F. Scott Fitzgerald', '9780743273565', 3),
            ('To Kill a Mockingbird', 'Harper Lee', '9780061120084', 2),
            ('1984', 'George Orwell', '9780451524935', 4),
        ]
        for title, author, isbn, total in sample:
            cur.execute(
                "INSERT OR IGNORE INTO books(title, author, isbn, total_copies, available_copies) VALUES (?, ?, ?, ?, ?)",
                (title, author, isbn, total, total)
            )
        conn.commit()
    conn.close()

# ---------- Book Queries ----------

def get_all_books() -> List[sqlite3.Row]:
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM books ORDER BY id').fetchall()
    conn.close()
    return rows

def get_book_by_id(book_id: int) -> Optional[sqlite3.Row]:
    conn = get_db_connection()
    row = conn.execute('SELECT * FROM books WHERE id = ?', (book_id,)).fetchone()
    conn.close()
    return row

def get_book_by_isbn(isbn: str) -> Optional[sqlite3.Row]:
    conn = get_db_connection()
    row = conn.execute('SELECT * FROM books WHERE isbn = ?', (isbn,)).fetchone()
    conn.close()
    return row

def insert_book(title: str, author: str, isbn: str, total_copies: int) -> int:
    """Insert a book and return new book id."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO books(title, author, isbn, total_copies, available_copies) VALUES(?, ?, ?, ?, ?)",
        (title, author, isbn, total_copies, total_copies)
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id

def update_book_availability(book_id: int, delta: int) -> bool:
    """
    Increment/decrement available_copies by delta ensuring bounds (0..total).
    Returns True if updated, False otherwise.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    row = cur.execute('SELECT available_copies, total_copies FROM books WHERE id=?', (book_id,)).fetchone()
    if not row:
        conn.close()
        return False
    new_avail = row['available_copies'] + delta
    if new_avail < 0 or new_avail > row['total_copies']:
        conn.close()
        return False
    cur.execute('UPDATE books SET available_copies = ? WHERE id = ?', (new_avail, book_id))
    conn.commit()
    conn.close()
    return True

# ---------- Borrowing ----------

def get_patron_borrow_count(patron_id: str) -> int:
    """Count active (not returned) borrow records for patron."""
    conn = get_db_connection()
    count = conn.execute(
        "SELECT COUNT(*) FROM borrow_records WHERE patron_id = ? AND return_date IS NULL",
        (patron_id,)
    ).fetchone()[0]
    conn.close()
    return int(count)

def insert_borrow_record(patron_id: str, book_id: int, borrow_date: datetime, due_date: datetime) -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO borrow_records(patron_id, book_id, borrow_date, due_date, return_date) VALUES (?, ?, ?, ?, NULL)",
        (patron_id, book_id, borrow_date.isoformat(), due_date.isoformat())
    )
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return rid

def get_active_borrow_record(patron_id: str, book_id: int) -> Optional[sqlite3.Row]:
    """Return the active (not yet returned) borrow record for patron/book if any."""
    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM borrow_records WHERE patron_id = ? AND book_id = ? AND return_date IS NULL ORDER BY id DESC LIMIT 1",
        (patron_id, book_id)
    ).fetchone()
    conn.close()
    return row

def update_borrow_record_return_date(patron_id: str, book_id: int, return_date: datetime) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    # Update only the most recent active borrow record for this patron/book
    cur.execute(
        "UPDATE borrow_records SET return_date = ? WHERE id = ("
        "SELECT id FROM borrow_records WHERE patron_id = ? AND book_id = ? AND return_date IS NULL ORDER BY id DESC LIMIT 1"
        ")",
        (return_date.isoformat(), patron_id, book_id)
    )
    updated = cur.rowcount
    conn.commit()
    conn.close()
    return updated > 0

def get_patron_current_borrows(patron_id: str):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT br.*, b.title, b.author, b.isbn "
        "FROM borrow_records br JOIN books b ON b.id = br.book_id "
        "WHERE br.patron_id = ? AND br.return_date IS NULL "
        "ORDER BY br.due_date ASC",
        (patron_id,)
    ).fetchall()
    conn.close()
    return rows

def get_patron_borrow_history(patron_id: str):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT br.*, b.title, b.author, b.isbn "
        "FROM borrow_records br JOIN books b ON b.id = br.book_id "
        "WHERE br.patron_id = ? "
        "ORDER BY br.borrow_date DESC",
        (patron_id,)
    ).fetchall()
    conn.close()
    return rows

# ---------- Search ----------

def search_books_title(term: str):
    conn = get_db_connection()
    like = f'%{term.lower()}%'
    rows = conn.execute(
        "SELECT * FROM books WHERE LOWER(title) LIKE ? ORDER BY id", (like,)
    ).fetchall()
    conn.close()
    return rows

def search_books_author(term: str):
    conn = get_db_connection()
    like = f'%{term.lower()}%'
    rows = conn.execute(
        "SELECT * FROM books WHERE LOWER(author) LIKE ? ORDER BY id", (like,)
    ).fetchall()
    conn.close()
    return rows

def search_books_isbn(isbn: str):
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM books WHERE isbn = ? ORDER BY id', (isbn,)).fetchall()
    conn.close()
    return rows


def get_patron_borrowed_books(patron_id: str):
    """
    Return a list of ACTIVE borrows for the patron.
    Each item has at least: book_id, title, author, borrow_date (datetime), due_date (datetime), is_overdue (bool)
    """
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT br.book_id, br.borrow_date, br.due_date, b.title, b.author "
        "FROM borrow_records br JOIN books b ON b.id = br.book_id "
        "WHERE br.patron_id = ? AND br.return_date IS NULL "
        "ORDER BY br.due_date ASC",
        (patron_id,)
    ).fetchall()
    conn.close()

    out = []
    for r in rows:
        try:
            borrow_dt = datetime.fromisoformat(r['borrow_date']) if isinstance(r['borrow_date'], str) else r['borrow_date']
            due_dt = datetime.fromisoformat(r['due_date']) if isinstance(r['due_date'], str) else r['due_date']
        except Exception:
            # Fallback: treat as not overdue if parsing fails
            borrow_dt = datetime.now()
            due_dt = datetime.now()
        out.append({
            'book_id': r['book_id'],
            'title': r['title'],
            'author': r['author'],
            'borrow_date': borrow_dt,
            'due_date': due_dt,
            'is_overdue': datetime.now() > due_dt
        })
    return out


def get_patron_borrow_history(patron_id: str):
    """
    Return a list of ALL borrows for the patron.
    Each item has at least: book_id, title, borrow_date (datetime), return_date (datetime or None)
    """
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT br.book_id, br.borrow_date, br.return_date, b.title "
        "FROM borrow_records br JOIN books b ON b.id = br.book_id "
        "WHERE br.patron_id = ? "
        "ORDER BY br.borrow_date DESC",
        (patron_id,)
    ).fetchall()
    conn.close()

    out = []
    for r in rows:
        try:
            borrow_dt = datetime.fromisoformat(r['borrow_date']) if isinstance(r['borrow_date'], str) else r['borrow_date']
        except Exception:
            borrow_dt = datetime.now()
        if r['return_date'] is None:
            return_dt = None
        else:
            try:
                return_dt = datetime.fromisoformat(r['return_date']) if isinstance(r['return_date'], str) else r['return_date']
            except Exception:
                return_dt = None
        out.append({
            'book_id': r['book_id'],
            'title': r['title'],
            'borrow_date': borrow_dt,
            'return_date': return_dt
        })
    return out
