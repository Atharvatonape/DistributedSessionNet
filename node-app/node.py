from flask import Flask, request, jsonify, render_template
import sqlite3
import uuid
import logging
from utils.get_database import create_sqlite_database, connect_database, insert_session

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

@app.route('/')
def index():
    create_sqlite_database('datab.db')
    return render_template('index.html')

@app.route('/session', methods=['POST'])
def handle_session():
    data = request.get_json()
    app.logger.info(f"Received data: {data}")  # Log received data to terminal # Print received data to terminal
    conn = connect_database('datab.db')
    session_id = uuid.uuid4().hex
    insert_session(conn, data, session_id)
    # Return a dummy JSON response for now
    return jsonify({"message": "Data received", "status": "Success"}, data), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)