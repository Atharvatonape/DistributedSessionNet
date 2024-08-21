# worker.py
from flask import Flask, request, jsonify
import os
import requests
import socket
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return "Welcome to the Worker App my dear!"


@app.route('/status', methods=['GET'])
def status():
    # Example data structure for worker status
    status_data = {
        'name': socket.gethostname(),
        'active': True,
        'requests_handled': get_requests_count(),
        'latest_request': "Example request"
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
