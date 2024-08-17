import psycopg2
import os
from dotenv import load_dotenv
import datetime

# Load environment variables from .env file
load_dotenv()

def create_rds_database():
    """Create a database connection to a PostgreSQL RDS database"""
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DATABASE_NAME'),
            user=os.getenv('DATABASE_USER'),
            password=os.getenv('DATABASE_PASSWORD'),
            host=os.getenv('DATABASE_INSTANCE'),
            port=os.getenv('DATABASE_PORT')
        )
        print("Connected to RDS PostgreSQL")
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                name TEXT,
                connection_time TIMESTAMP,
                session_end_time TIMESTAMP
            )
        ''')
        conn.commit()
    except psycopg2.Error as e:
        print(e)
    finally:
        if conn:
            conn.close()

def connect_database():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DATABASE_NAME'),
            user=os.getenv('DATABASE_USER'),
            password=os.getenv('DATABASE_PASSWORD'),
            host=os.getenv('DATABASE_INSTANCE'),
            port=os.getenv('DATABASE_PORT')
        )
        return conn
    except psycopg2.Error as e:
        print(e)
    return None

def insert_session(conn, data, session_id, app):
    name = data.get('name')
    connection_time = data.get('timestamp')  # Ensure this key exists in data
    session_end_time = data.get('session_end')  # Ensure this key exists in data
    sql = ''' INSERT INTO sessions(session_id, name, connection_time, session_end_time)
              VALUES(%s,%s,%s,%s) '''  # PostgreSQL uses %s for placeholders
    cur = conn.cursor()
    try:
        cur.execute(sql, (session_id, name, connection_time, session_end_time))
        conn.commit()
        return cur.lastrowid
    except psycopg2.Error as e:
        print(f"An error occurred: {e}")
    finally:
        app.logger.info(f"Received daata into AWS")
        cur.close()

# Example usage
#create_rds_database()

#data = {'name': 'Susan Dominguez', 'timestamp': '2024-08-16 13:35:40 UTC', 'session_end': '2024-08-16 13:45:40 UTC'}

#conn = connect_database()
#insert_session(conn, data, '1234')
