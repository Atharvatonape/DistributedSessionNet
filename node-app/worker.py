# worker.py
from flask import Flask, request, jsonify
import os
import requests
import socket
from flask_cors import CORS
import logging
import threading  # Import threading for handling timers
from decouple import config  # Import the config function from decouple

app = Flask(__name__)
app.logger.setLevel(logging.INFO)
CORS(app)

latest_request_name = None
count = 0
status_worker = True
reset_timer = None  # Global timer for resetting count
central_app_ip = config('CENTRAL_APP_IP', default='localhost')

def reset_worker_status():
    global count, status_worker
    status_worker = True
    count = 0  # Reset count to zero
    # status_data = {
    #     'name': socket.gethostname(),
    #     'active': True,
    #     "identifier": "reset"
    # }
    # response = requests.post('http://distributedsessionnet-central-1:7110/update_status', json=status_data)
    # app.logger.info(f"Response from central app after updating the worker status: {response.json()}")

@app.after_request
def apply_csp(response):
    response.headers["Content-Security-Policy"] = "upgrade-insecure-requests"
    return response

@app.route('/')
def index():
    return "Welcome to the Worker App my dear!"

@app.route('/receive_data', methods=['POST'])
def receive_data():
    global latest_request_name, count, status_worker, reset_timer
    # Process only if the worker is active
    if status_worker:
        data = request.json
        app.logger.info(f"Received data: {data}")

        if 'name' in data:
            latest_request_name = data['name']
            count += 1

        # Check if count reached 2 and trigger status change
        if count >= 2:
            status_worker = False  # Set worker status to inactive immediately
            app.logger.info("Worker status set to inactive")

            # Send status to the central app
            status_data = {
                'name': socket.gethostname(),
                'active': status_worker,
            }
            response = requests.get(central_app_ip +'/update_status', json=status_data)
            app.logger.info(f"Response from central app: {response.json()}")

            # Start a timer to reset the worker status after 10 seconds
            if reset_timer is not None:
                reset_timer.cancel()  # Cancel any existing timer
            reset_timer = threading.Timer(10.0, reset_worker_status)
            reset_timer.start()

        return jsonify({"received": True, "data": data})

    else:
        app.logger.info("Worker is inactive; rejecting request.")
        return jsonify({"received": False, "message": "Worker is not active"})


@app.route('/status', methods=['GET'])
def status():
    global latest_request_name, count, status_worker
    status_data = {
        'name': socket.gethostname(),
        'active': status_worker,
        'requests_handled': count,
        'latest_request': latest_request_name if latest_request_name else "No request received yet"
    }
    return jsonify(status_data)

@app.route('/compute', methods=['POST'])
def compute():
    data = request.json
    result = sum(data['numbers'])
    return jsonify({'result': result, 'node_id': os.getenv('NODE_ID')})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8110))
    app.run(debug=True, host='0.0.0.0', port=port)
