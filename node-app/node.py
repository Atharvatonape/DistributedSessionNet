from flask import Flask, request, jsonify
import sqlite3
import uuid

app = Flask(__name__)

DATABASE = 'node_session.db'

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

@app.route('/session', methods=['POST'])
def create_session():
    try:
        data = request.get_json()
        if 'user_data' not in data:
            return jsonify({"error": "Missing user_data"}), 400
        session_id = str(uuid.uuid4())
        # Simulate storing session data or other processing
        return jsonify({"message": "Session created", "session_id": session_id}), 201
    except Exception as e:
        app.logger.error(f"Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500


# @app.route('/session', methods=['POST'])
# def create_session():
#     session_id = str(uuid.uuid4())
#     user_data = request.json['user_data']

#     db = get_db()
#     db.execute('INSERT INTO sessions (id, data, active) VALUES (?, ?, ?)',
#                [session_id, user_data, 1])
#     db.commit()
#     return jsonify({"message": "Session created", "session_id": session_id})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)