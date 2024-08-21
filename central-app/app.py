from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import docker
from utils.docker_containers import get_running_container_names, get_urls_of_running_containers

app = Flask(__name__)
socketio = SocketIO(app)
client = docker.from_env()
workers_status = {}

@app.route('/')
def index():
    return render_template('create_workers.html')

@socketio.on('start_create_workers')
def handle_create_workers(data):
    num_workers = data.get('num_workers', 2)
    base_port = 5001
    workers = {}

    for i in range(num_workers):
        container_name = f"worker_{i+1}"
        emit('update', {'message': f'Creating {container_name}...'}, broadcast=True)
        try:
            existing_container = client.containers.get(container_name)
            existing_container.stop()
            existing_container.remove()
        except docker.errors.NotFound:
            pass

        port = base_port + i
        container = client.containers.run(
            "worker_image",
            detach=True,
            ports={'8110/tcp': port},
            environment={'NODE_ID': f'node_{i+1}', 'PORT': '8110'},
            name=container_name
        )
        workers[container_name] = f'http://localhost:{port}'
        emit('update', {'message': f'{container_name} created at http://localhost:{port}'}, broadcast=True)

    emit('update', {'message': f'{num_workers} workers created'}, broadcast=True)

@socketio.on('kill_worker')
def handle_kill_worker(data):
    worker_name = data['worker_name']
    emit('update', {'message': f'Killing {worker_name}...'}, broadcast=True)
    try:
        container = client.containers.get(worker_name)
        container.stop()
        container.remove()
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

@app.route('/workers_get')
def list_workers():
    return jsonify(get_running_container_names())


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=7110)
