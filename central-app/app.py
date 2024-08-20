# central.py
from flask import Flask, request, jsonify
import requests
import subprocess
import docker
import atexit

app = Flask(__name__)
client = docker.from_env()
workers = {}
containers = []

@app.route('/')
def index():
    return "Welcome to the Central App!"

@app.route('/sample', methods=['POST'])  # This route only accepts POST requests
def sample():
    return "This is a sample route."


@app.route('/create_workers')
def create_workers():
    #num_workers = request.json.get('num_workers', 1)
    num_workers = 2
    workers = {}
    base_port = 5001  # Starting port number for worker nodes

    for i in range(num_workers):
        container_name = f"worker_{i}"
        try:
            existing_container = client.containers.get(container_name)
            existing_container.stop()
            existing_container.remove()
        except docker.errors.NotFound:
            pass

        port = base_port + i
        container = client.containers.run(
            "worker_image",  # Name of the Docker image for worker nodes
            detach=True,
            ports={'8110/tcp': port},
            environment={'NODE_ID': f'node_{i+1}', 'PORT': '8110'},
            name=f"worker_{i+1}"
        )
        containers.append(container)
        workers[f'node_{i+1}'] = f'http://localhost:{port}'

    return jsonify({'message': f'{num_workers} workers created', 'workers': workers})

def cleanup_docker_containers():
    for container in containers:
        container.stop()
        container.remove()


@app.route('/distribute_task', methods=['POST'])
def distribute_task():
    data = request.json.get('numbers', [1, 2])
    results = []
    for node_id, url in workers.items():
        response = requests.post(f'{url}/compute', json={'numbers': data})
        results.append(response.json())
    return jsonify(results)

atexit.register(cleanup_docker_containers)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=7110)
