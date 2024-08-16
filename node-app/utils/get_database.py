import sqlite3
import datetime

def create_sqlite_database(filename):
    """ create a database connection to an SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(filename)
        print(sqlite3.sqlite_version)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                name TEXT,
                connection_time datetime,
                session_end_time datetime
            )
        ''')
    except sqlite3.Error as e:
        print(e)
    finally:
        if conn:
            conn.close()

def connect_database(filename):
    conn = None
    try:
        conn = sqlite3.connect(filename)
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn

def insert_session(conn, data, session_id):
    name = data.get('name')
    connection_time = data.get('timestamp')  # Ensure this key exists in data
    session_end_time = data.get('session_end')  # Ensure this key exists in data
    sql = ''' INSERT INTO sessions(session_id, name, connection_time, session_end_time)
              VALUES(?,?,?,?) '''  # Corrected the number of placeholders
    cur = conn.cursor()
    try:
        cur.execute(sql, (session_id, name, connection_time, session_end_time))
        conn.commit()
        return cur.lastrowid
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        cur.close()  # Ensuring that the cursor is closed after operation

# create_sqlite_database('first-node.db')

# data = {'name': 'Susan Dominguez', 'address': 'PSC 1422, Box 7432\nAPO AA 59554', 'email': 'austin42@example.net', 'phone': '928.380.7055x5983', 'job': 'Estate manager/land agent', 'company': 'Johnston, Mathis and Burns', 'text': 'Wall long yes voice. Way agency direction then too specific.\nPass find offer voice carry evening your. Level force board just financial if life.', 'timestamp': '2024-08-16 13:35:40 UTC', 'session_end': '2024-08-16 13:45:40 UTC'}

# conn = connect_database('first-node.db')
# insert_session(conn, data, '1234')