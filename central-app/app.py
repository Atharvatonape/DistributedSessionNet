from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import docker

app = Flask(__name__)
socketio = SocketIO(app)
client = docker.from_env()

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

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=7110)
