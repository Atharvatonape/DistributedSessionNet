from flask import Flask, render_template, jsonify, request
import docker
from utils.docker_containers import get_running_container_names
from utils.fake_data import fake_data_gen
from utils.load_balancing import TaskManager
import requests
import logging

app = Flask(__name__)
client = docker.from_env()
app.logger.setLevel(logging.INFO)

@app.after_request
def after_request(response):
    """Set CORS headers for every response."""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/')
def index():
    return render_template('create_workers.html')

@app.route('/create_workers', methods=['POST'])
def create_workers():
    num_workers = request.json.get('num_workers', 2)
    task_manager = TaskManager()
    workers = task_manager.create_workers(num_workers)
    response = {'message': f'{num_workers} workers created', 'workers': workers}
    return jsonify(response)

@app.route('/kill_worker', methods=['POST'])
def kill_worker():
    worker_name = request.json['worker_name']
    try:
        container = client.containers.get(worker_name)
        container.stop()
        container.remove()
        app.logger.info(f"Worker {worker_name} killed")
        return jsonify({'message': f'{worker_name} successfully killed'}), 200
    except Exception as e:
        return jsonify({'message': f'Error killing {worker_name}: {str(e)}'}), 500

@app.route('/kill_all_workers', methods=['POST'])
def kill_all_workers():
    containers = client.containers.list()  # List all containers
    for container in containers:
        if "worker_" in container.name:
            try:
                container.stop()
                container.remove()
            except Exception as e:
                return jsonify({'message': f'Error killing {container.name}: {str(e)}'}), 500
    return jsonify({'message': 'All workers have been killed'}), 200

@app.route('/workers', methods=['GET'])
def workers():
    jsonn = get_running_container_names()
    return jsonify(jsonn)

@app.route('/worker_status/<worker_name>', methods=['GET'])
def worker_status(worker_name):
    task_manager = TaskManager()  # Ensure this uses your existing TaskManager instance
    try:
        # Assuming the worker status includes whether it's active and its last response etc.
        response = requests.get(f"http://{worker_name}:8110/status")
        response_json = response.json()
        # Add the request history to the JSON response
        response_json['request_history'] = list(task_manager.request_history[worker_name])
        return jsonify(response_json), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/worker_status2/<worker_name>', methods=['GET'])
def worker_status2(worker_name):
    task_manager = TaskManager()  # Singleton instance of TaskManager
    try:
        # Retrieve the worker's history from the defaultdict
        worker_history = task_manager.request_history[worker_name]
        #app.logger.info(f"Worker history for {worker_name}: {worker_history}")

        # Process the history to extract the task data
        history_data = [
            {
                'name': entry['name'],
                'email': entry['email'],
                'job': entry['job'],
                'address': entry['address'],
                'phone_number': entry['phone_number'],
                'company': entry['company'],
                'text': entry['text']
            } for entry in worker_history
        ]

        return jsonify({
            'active': task_manager.get_worker_state(worker_name) == 'active',
            'request_history': history_data
        }), 200
    except Exception as e:
        app.logger.error(f"Error in worker_status2: {str(e)}")  # Log the error
        return jsonify({'error': str(e)}), 500


@app.route('/workers_get', methods=['GET'])
def get_workers():
    task_manager = TaskManager()  # Assuming singleton pattern
    workers = get_running_container_names()
    active_count = sum(1 for w in workers if task_manager.get_worker_state(w) == 'active')
    return jsonify({
        'activeWorkers': active_count,
        'successfulTasks': task_manager.successful_task,
        'taskListDuplicateCount': len(task_manager.task_list_duplicate),
        'workers': workers
    })


@app.route('/idle_time', methods=['POST'])
def idle_time():
    data = request.json
    app.logger.info(f"Data received: {data}")
    idle_time = data.get('idletime')
    app.logger.info(f"Idle Time: {idle_time}")
    task_manager = TaskManager()  # Assuming singleton pattern
    task_manager.idle_time = idle_time
    app.logger.info(f"Idle Time set to {task_manager.idle_time}")
    return jsonify({"success": True, "message": f"Workers will get deleted after remaining idle for {idle_time} sec"}), 200


@app.route('/send_fake_data', methods=['POST'])
def send_fake_data():
    try:
        fake_data = fake_data_gen()
        task_manager = TaskManager()
        task_manager.load_task(fake_data)
        response = 'response'
        return jsonify(response)
    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/update_status', methods=['POST'])
def status():
    data = request.json
    worker_id = data.get('name')
    state = data.get('active')
    state = "active" if state in [True, "True"] else state

    task_manager = TaskManager()
    task_manager.update_worker_state(worker_id, state)
    return jsonify({"success": True, "message": "Worker state updated"}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=7110)
