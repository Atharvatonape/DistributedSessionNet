# worker.py
from flask import Flask, request, jsonify
import os
import requests
import socket
from flask_cors import CORS
import logging



app = Flask(__name__)
app.logger.setLevel(logging.INFO)

CORS(app)

latest_request_name = None
count = 0

@app.route('/')
def index():
    return "Welcome to the Worker App my dear!"

@app.route('/receive_data', methods=['POST'])
def receive_data():
    global latest_request_name, count
    data = request.json
    # Log the incoming data using app.logger
    app.logger.info(f"Received data: {data}")
    if 'name' in data:
        latest_request_name = data['name']
        count += 1

    return jsonify({"received": True, "data": data})


@app.route('/status', methods=['GET'])
def status():
    global latest_request_name, count
    status_data = {
        'name': socket.gethostname(),
        'active': True,
        'requests_handled': count,
        'latest_request': latest_request_name if latest_request_name else "No request received yet"
    }
    return jsonify(status_data)

def get_requests_count():
    """ Function to track the number of requests handled by the worker. """
    return 100

@app.route('/compute', methods=['POST'])
def compute():
    data = request.json
    result = sum(data['numbers'])
    return jsonify({'result': result, 'node_id': os.getenv('NODE_ID')})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8110))
    node_id = os.environ.get('NODE_ID', '1')
    app.run(debug=True, host='0.0.0.0', port=port)
