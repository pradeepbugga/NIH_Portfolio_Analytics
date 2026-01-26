# this script provides functions to get database connections for PostgreSQL, SQLite, and SQLAlchemy

import psycopg2
import sqlite3
import sqlalchemy
from core.config import POSTGRES_CONFIG


def get_db_connection():
    return psycopg2.connect(**POSTGRES_CONFIG)

def get_sqlite_connection(db_path: str):
    conn = sqlite3.connect(db_path)
    return conn

def get_sqlalchemy_engine():
    return sqlalchemy.create_engine(
        f"postgresql+psycopg2://{POSTGRES_CONFIG['user']}:{POSTGRES_CONFIG['password']}@{POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}/{POSTGRES_CONFIG['dbname']}",
        pool_pre_ping=True
    )