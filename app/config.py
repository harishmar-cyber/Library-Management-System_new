import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

class Config:
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.getenv('SECRET_KEY', 'lavender_lms_super_secret_dev_key_2026')
    
    # MySQL Database Config
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', '3306'))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'library_management_db')
    
    # Auto fallback to SQLite if MySQL is unavailable
    DB_AUTO_FALLBACK = os.getenv('DB_AUTO_FALLBACK', 'True').lower() in ('true', '1', 'yes')
    SQLITE_PATH = str(BASE_DIR / 'library.sqlite3')
    
    # Business Rules
    LOAN_PERIOD_DAYS = 14
    FINE_PER_DAY = 1.00
    MAX_BOOKS_PER_STUDENT = 3
    MAX_RESERVATIONS_PER_STUDENT = 2
