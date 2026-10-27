import sqlite3
import pymysql
import pymysql.cursors
import logging
import re
from pathlib import Path
from app.config import Config

logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance = None
    _use_sqlite = False

    def __init__(self):
        self.use_sqlite = False
        self._test_mysql_connection()

    def _test_mysql_connection(self):
        try:
            conn = pymysql.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                charset='utf8mb4',
                connect_timeout=3
            )
            conn.close()
            self.use_sqlite = False
            logger.info("Successfully verified MySQL connection.")
        except Exception as e:
            if Config.DB_AUTO_FALLBACK:
                logger.warning(f"MySQL connection unavailable ({e}). Falling back to SQLite local database.")
                self.use_sqlite = True
            else:
                logger.error(f"MySQL connection error: {e}")
                raise e

    def get_connection(self):
        if not self.use_sqlite:
            try:
                return pymysql.connect(
                    host=Config.DB_HOST,
                    port=Config.DB_PORT,
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD,
                    database=Config.DB_NAME,
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor,
                    autocommit=True
                )
            except Exception as e:
                if Config.DB_AUTO_FALLBACK:
                    logger.warning(f"Failed to connect to MySQL database '{Config.DB_NAME}': {e}. Switching to SQLite fallback.")
                    self.use_sqlite = True
                else:
                    raise e

        # SQLite fallback connection
        conn = sqlite3.connect(Config.SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def execute_query(self, query: str, params: tuple = None) -> int:
        """Execute INSERT, UPDATE, DELETE queries and return affected row count or lastrowid."""
        conn = self.get_connection()
        try:
            if self.use_sqlite:
                # Convert %s placeholders to ? for sqlite3
                sqlite_query = self._mysql_to_sqlite_query(query)
                cursor = conn.cursor()
                cursor.execute(sqlite_query, params or ())
                conn.commit()
                last_id = cursor.lastrowid
                rowcount = cursor.rowcount
                cursor.close()
                return last_id if last_id else rowcount
            else:
                with conn.cursor() as cursor:
                    cursor.execute(query, params or ())
                    last_id = cursor.lastrowid
                    rowcount = cursor.rowcount
                    return last_id if last_id else rowcount
        finally:
            conn.close()

    def fetch_all(self, query: str, params: tuple = None) -> list:
        """Fetch all matching rows as dictionaries."""
        conn = self.get_connection()
        try:
            if self.use_sqlite:
                sqlite_query = self._mysql_to_sqlite_query(query)
                cursor = conn.cursor()
                cursor.execute(sqlite_query, params or ())
                rows = [dict(row) for row in cursor.fetchall()]
                cursor.close()
                return rows
            else:
                with conn.cursor() as cursor:
                    cursor.execute(query, params or ())
                    return cursor.fetchall()
        finally:
            conn.close()

    def fetch_one(self, query: str, params: tuple = None) -> dict:
        """Fetch a single matching row as a dictionary."""
        conn = self.get_connection()
        try:
            if self.use_sqlite:
                sqlite_query = self._mysql_to_sqlite_query(query)
                cursor = conn.cursor()
                cursor.execute(sqlite_query, params or ())
                row = cursor.fetchone()
                cursor.close()
                return dict(row) if row else None
            else:
                with conn.cursor() as cursor:
                    cursor.execute(query, params or ())
                    return cursor.fetchone()
        finally:
            conn.close()

    def _mysql_to_sqlite_query(self, query: str) -> str:
        """Adapts MySQL query syntax and placeholders for SQLite."""
        # Replace %s placeholder with ?
        adapted = re.sub(r'(?<!%)(%s)', '?', query)
        adapted = adapted.replace('%%', '%')
        return adapted

    def init_database(self):
        """Initializes database schema and seed data."""
        schema_file = Config.BASE_DIR / 'schema.sql'
        if not schema_file.exists():
            logger.error("schema.sql not found.")
            return

        with open(schema_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        if not self.use_sqlite:
            # MySQL setup
            try:
                conn = pymysql.connect(
                    host=Config.DB_HOST,
                    port=Config.DB_PORT,
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD,
                    charset='utf8mb4'
                )
                with conn.cursor() as cursor:
                    # Split statements
                    statements = [s.strip() for s in sql_content.split(';') if s.strip()]
                    for stmt in statements:
                        try:
                            cursor.execute(stmt)
                        except Exception as err:
                            logger.debug(f"Statement execution notice: {err}")
                conn.commit()
                conn.close()
                logger.info("MySQL database initialized successfully.")
                return
            except Exception as e:
                logger.warning(f"Could not initialize MySQL ({e}). Initializing SQLite fallback.")
                self.use_sqlite = True

        # SQLite schema initialization
        conn = sqlite3.connect(Config.SQLITE_PATH)
        cursor = conn.cursor()

        # Create tables adapted for SQLite
        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
          user_id INTEGER PRIMARY KEY AUTOINCREMENT,
          username TEXT NOT NULL UNIQUE,
          password_hash TEXT NOT NULL,
          full_name TEXT NOT NULL,
          email TEXT NOT NULL UNIQUE,
          role TEXT DEFAULT 'librarian',
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS books (
          book_id INTEGER PRIMARY KEY AUTOINCREMENT,
          isbn TEXT NOT NULL UNIQUE,
          title TEXT NOT NULL,
          author TEXT NOT NULL,
          category TEXT NOT NULL,
          publication_year INTEGER NOT NULL,
          total_copies INTEGER NOT NULL DEFAULT 1,
          available_copies INTEGER NOT NULL DEFAULT 1,
          shelf_location TEXT DEFAULT 'Section A',
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS students (
          student_id INTEGER PRIMARY KEY AUTOINCREMENT,
          student_number TEXT NOT NULL UNIQUE,
          full_name TEXT NOT NULL,
          email TEXT NOT NULL UNIQUE,
          phone TEXT NOT NULL,
          department TEXT NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS book_issues (
          issue_id INTEGER PRIMARY KEY AUTOINCREMENT,
          book_id INTEGER NOT NULL,
          student_id INTEGER NOT NULL,
          issue_date TEXT NOT NULL,
          due_date TEXT NOT NULL,
          return_date TEXT NULL,
          status TEXT DEFAULT 'issued',
          fine_amount REAL DEFAULT 0.00,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
          FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS reservations (
          reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
          book_id INTEGER NOT NULL,
          student_id INTEGER NOT NULL,
          reservation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          queue_position INTEGER NOT NULL DEFAULT 1,
          status TEXT DEFAULT 'pending',
          FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
          FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS transactions (
          transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
          action_type TEXT NOT NULL,
          entity_type TEXT NOT NULL,
          entity_id INTEGER NOT NULL,
          details TEXT NULL,
          user_id INTEGER NULL,
          undone INTEGER DEFAULT 0,
          timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS book_relations (
          relation_id INTEGER PRIMARY KEY AUTOINCREMENT,
          source_book_id INTEGER NOT NULL,
          target_book_id INTEGER NOT NULL,
          relation_type TEXT NOT NULL DEFAULT 'co_borrowed',
          weight REAL DEFAULT 1.00,
          FOREIGN KEY (source_book_id) REFERENCES books(book_id) ON DELETE CASCADE,
          FOREIGN KEY (target_book_id) REFERENCES books(book_id) ON DELETE CASCADE,
          UNIQUE(source_book_id, target_book_id)
        );
        """)

        # Seed initial admin user if empty
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            INSERT INTO users (username, password_hash, full_name, email, role)
            VALUES 
            ('admin', 'scrypt:32768:8:1$9wdvIxbntQrbbFyI$2855f52f6803bc01c143931f74b60f85c352d88a17896c8d79a25d6c9c0e35f5572f31f1e27bbc6505c83f48a5805854bf77d8e50bbb78bd9e5fc5967b4aaff2', 'Chief Librarian Harishma', 'admin@library.edu', 'admin'),
            ('librarian', 'scrypt:32768:8:1$9wdvIxbntQrbbFyI$2855f52f6803bc01c143931f74b60f85c352d88a17896c8d79a25d6c9c0e35f5572f31f1e27bbc6505c83f48a5805854bf77d8e50bbb78bd9e5fc5967b4aaff2', 'Assistant Librarian John', 'john@library.edu', 'librarian');
            """)
        else:
            cursor.execute("""
            UPDATE users SET password_hash = 'scrypt:32768:8:1$9wdvIxbntQrbbFyI$2855f52f6803bc01c143931f74b60f85c352d88a17896c8d79a25d6c9c0e35f5572f31f1e27bbc6505c83f48a5805854bf77d8e50bbb78bd9e5fc5967b4aaff2'
            WHERE username IN ('admin', 'librarian')
            """)

        # Seed books if empty
        cursor.execute("SELECT COUNT(*) FROM books")
        if cursor.fetchone()[0] == 0:
            cursor.executescript("""
            INSERT INTO books (book_id, isbn, title, author, category, publication_year, total_copies, available_copies, shelf_location) VALUES
            (1, '978-0262033848', 'Introduction to Algorithms', 'Thomas H. Cormen', 'Computer Science', 2009, 5, 3, 'Shelf CS-01'),
            (2, '978-0132350884', 'Clean Code', 'Robert C. Martin', 'Software Engineering', 2008, 4, 4, 'Shelf SE-03'),
            (3, '978-0131103627', 'The C Programming Language', 'Brian W. Kernighan', 'Programming', 1988, 3, 2, 'Shelf PR-02'),
            (4, '978-0201633610', 'Design Patterns', 'Erich Gamma', 'Software Engineering', 1994, 4, 3, 'Shelf SE-04'),
            (5, '978-1449355739', 'Learning Python', 'Mark Lutz', 'Programming', 2013, 6, 5, 'Shelf PR-05'),
            (6, '978-0134685991', 'Effective Java', 'Joshua Bloch', 'Programming', 2017, 3, 3, 'Shelf PR-06'),
            (7, '978-0262035613', 'Deep Learning', 'Ian Goodfellow', 'Artificial Intelligence', 2016, 4, 3, 'Shelf AI-01'),
            (8, '978-1491957660', 'Hands-On Machine Learning', 'Aurélien Géron', 'Artificial Intelligence', 2019, 5, 4, 'Shelf AI-02'),
            (9, '978-0321573513', 'Algorithms 4th Edition', 'Robert Sedgewick', 'Computer Science', 2011, 4, 3, 'Shelf CS-02'),
            (10, '978-0133594140', 'Operating System Concepts', 'Abraham Silberschatz', 'Systems', 2018, 5, 4, 'Shelf OS-01');

            INSERT INTO students (student_id, student_number, full_name, email, phone, department) VALUES
            (1, 'STU2026001', 'Alice Johnson', 'alice.j@student.edu', '9876543210', 'Computer Science & Engg'),
            (2, 'STU2026002', 'Brian Miller', 'brian.m@student.edu', '9876543211', 'Information Technology'),
            (3, 'STU2026003', 'Catherine Davis', 'catherine.d@student.edu', '9876543212', 'Artificial Intelligence & DS'),
            (4, 'STU2026004', 'David Wilson', 'david.w@student.edu', '9876543213', 'Computer Science & Engg'),
            (5, 'STU2026005', 'Elena Rostova', 'elena.r@student.edu', '9876543214', 'Electronics & Comm Engg');

            INSERT INTO book_issues (issue_id, book_id, student_id, issue_date, due_date, return_date, status, fine_amount) VALUES
            (1, 1, 1, '2026-10-10', '2026-10-24', NULL, 'overdue', 15.00),
            (2, 1, 2, '2026-10-18', '2026-11-01', NULL, 'issued', 0.00),
            (3, 3, 3, '2026-10-20', '2026-11-03', NULL, 'issued', 0.00),
            (4, 7, 4, '2026-10-22', '2026-11-05', NULL, 'issued', 0.00),
            (5, 4, 5, '2026-10-15', '2026-10-29', NULL, 'issued', 0.00);

            INSERT INTO reservations (reservation_id, book_id, student_id, reservation_date, queue_position, status) VALUES
            (1, 1, 3, '2026-10-21 09:30:00', 1, 'pending'),
            (2, 1, 4, '2026-10-22 14:15:00', 2, 'pending'),
            (3, 1, 5, '2026-10-23 11:00:00', 3, 'pending'),
            (4, 3, 2, '2026-10-24 16:45:00', 1, 'pending');

            INSERT INTO book_relations (source_book_id, target_book_id, relation_type, weight) VALUES
            (1, 9, 'Same Topic: Algorithms', 0.95),
            (9, 1, 'Same Topic: Algorithms', 0.95),
            (1, 10, 'Prerequisite: CS Core', 0.80),
            (10, 1, 'Prerequisite: CS Core', 0.80),
            (2, 4, 'Same Domain: Software Architecture', 0.90),
            (4, 2, 'Same Domain: Software Architecture', 0.90),
            (2, 6, 'Clean Code Best Practices', 0.85),
            (6, 2, 'Clean Code Best Practices', 0.85),
            (3, 10, 'C & Low-level Operating Systems', 0.88),
            (10, 3, 'C & Low-level Operating Systems', 0.88),
            (5, 7, 'Python Foundation for AI', 0.85),
            (7, 5, 'Python Foundation for AI', 0.85),
            (7, 8, 'Machine Learning & Deep Learning', 0.98),
            (8, 7, 'Machine Learning & Deep Learning', 0.98),
            (8, 5, 'Hands-on Python Implementation', 0.82),
            (5, 8, 'Hands-on Python Implementation', 0.82),
            (1, 7, 'Algorithmic Foundation for AI', 0.75),
            (7, 1, 'Algorithmic Foundation for AI', 0.75);
            """)

        conn.commit()
        conn.close()
        logger.info("SQLite database fallback initialized and seeded successfully.")

# Global singleton database manager instance
db = DatabaseManager()
