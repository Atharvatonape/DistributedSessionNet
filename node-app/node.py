from flask import Flask, request, jsonify, render_template
import sqlite3
import uuid
import logging
from utils.get_database import create_rds_database, connect_database, insert_session

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

@app.route('/')
def index():
    create_rds_database()
    return render_template('index.html')

@app.route('/session', methods=['POST'])
def handle_session():
    data = request.get_json()
    print(data)
    app.logger.info(f"Received data: {data}")  # Log received data to terminal # Print received data to terminal
    conn = connect_database()
    session_id = uuid.uuid4().hex
    insert_session(conn, data, session_id, app)
    # Return a dummy JSON response for now
    return jsonify({"message": "Data received", "status": "Success"}, data), 200

@app.route('/load', methods=['POST'])
def load_balancer():
    # Parse the incoming JSON data
    data = request.get_json()
    total_nodes = data['nodes']  # Extract the number of nodes from the data
    app.logger.info('Recieved the nodes')
    # Assume some processing here with total_nodes
    # For now, just log it or print it to console (in real scenarios, you might configure resources or similar)
    print("Total nodes to load balance:", total_nodes)

    # Return a simple True as a JSON response
    return jsonify(True), 200
    


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5173)