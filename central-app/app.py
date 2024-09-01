from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import docker
from utils.docker_containers import get_running_container_names, get_urls_of_running_containers
from utils.fake_data import fake_data_gen
from utils.load_balancing import round_robin, TaskManager
import requests
import logging
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app)
client = docker.from_env()
workers_status = {}
app.logger.setLevel(logging.INFO)

@app.route('/')
def index():
    return render_template('create_workers.html')

@socketio.on('start_create_workers')
def handle_create_workers(data):
    num_workers = data.get('num_workers', 2)
    emit('update', {'message': f'Creating {num_workers} workers...'}, broadcast=True)
    task_manager = TaskManager()
    # Delegate worker creation to the TaskManager
    workers = task_manager.create_workers(num_workers)
    app.logger.info(f"Workers: {workers}")
    for worker_name, url in workers.items():
        emit('update', {'message': f'{worker_name} created at {url}'}, broadcast=True)

    emit('update', {'message': f'{num_workers} workers created'}, broadcast=True)

@socketio.on('kill_worker')
def handle_kill_worker(data):
    worker_name = data['worker_name']
    emit('update', {'message': f'Killing {worker_name}...'}, broadcast=True)
    try:
        container = client.containers.get(worker_name)
        container.stop()
        container.remove()
        app.logger.info(f"Worker {worker_name} killed")
        emit('update', {'message': f'{worker_name} successfully killed'}, broadcast=True)
    except Exception as e:
        emit('update', {'message': f'Error killing {worker_name}: {str(e)}'}, broadcast=True)

@socketio.on('kill_all_workers')
def handle_kill_all_workers():
    emit('update', {'message': 'Killing all workers...'}, broadcast=True)
    containers = client.containers.list()  # List all containers
    for container in containers:
        if "worker_" in container.name:
            try:
                container.stop()
                container.remove()
                emit('update', {'message': f'{container.name} successfully killed'}, broadcast=True)
            except Exception as e:
                emit('update', {'message': f'Error killing {container.name}: {str(e)}'}, broadcast=True)
    emit('update', {'message': 'All workers have been killed'}, broadcast=True)

@app.route('/workers', methods=['GET'])
def workers():
    jsonn = get_urls_of_running_containers()
    return jsonify(jsonn)

@app.route('/workers_get', methods=['GET'])
def get_workers():
    task_manager = TaskManager()  # Assuming singleton pattern
    workers = get_running_container_names()
    active_count = sum(1 for w in workers if task_manager.get_worker_state(w) == 'active')
    return jsonify({
        'activeWorkers': active_count,
        'successfulTasks': task_manager.successful_task,
        'taskListDuplicateCount': len(task_manager.task_list_duplicate)
    })


@app.route('/send_fake_data', methods=['POST'])
def send_fake_data():
    try:
        fake_data = fake_data_gen()
        task_manager = TaskManager()
        #app.logger.info(f"Worker states: {task_manager.worker_states}")
        app.logger.info(f"Before Loading: {len(task_manager.task_list)}, {len(task_manager.task_list_duplicate)}")
        task_manager.load_task(fake_data)
        response = 'response'
        app.logger.info(f"After Loading: {len(task_manager.task_list)}, {len(task_manager.task_list_duplicate)}")
        #app.logger.info(f"Response: {response}")
        return jsonify(response)
    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/update_status', methods=['POST'])
def status():
    data = request.json
    worker_id = data.get('name')
    state = data.get('active')
    if state == True or state == "True":
        state = "active"
    try:
        identifier = data.get('identifier')
        #app.logger.info(f"Received update status request with Reset data: {identifier}")
        #app.logger.info(f"Data: {data}")
    except:
        pass

    task_manager = TaskManager()
    task_manager.update_worker_state(worker_id, state)
    #app.logger.info(f"Received update status request with data: \n{data}")
    #app.logger.info(f"Worker state updated: {worker_id} - {state}")
    #app.logger.info(f"Worker states: {task_manager.worker_states}")
    return jsonify({"success": True, "message": "Worker state updated"})



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=7110, ssl_context=('cert.pem', 'key.pem'))
