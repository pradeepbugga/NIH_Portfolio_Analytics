import psycopg2
from core.config import POSTGRES_CONFIG


def get_db_connection():

    """
    Get a connection to the PostgreSQL database using psycopg2.

    Returns:
        psycopg2.extensions.connection: A connection object to the PostgreSQL database.
    """

    conn = psycopg2.connect(**POSTGRES_CONFIG)
    cur = conn.cursor()

    cur.execute("SET work_mem = '64MB';")
    cur.close()
    
    return conn

