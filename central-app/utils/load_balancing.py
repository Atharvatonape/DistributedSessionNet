from utils.docker_containers import get_running_container_names
import requests
from utils.fake_data import fake_data_gen
import threading
from flask import Flask, jsonify, request
from flask_socketio import SocketIO
import time
import docker
import logging
import queue
import collections

app = Flask(__name__)
app.logger.setLevel(logging.INFO)
socketio = SocketIO(app)

count = 0

def round_robin():
    global count
    container_names = get_running_container_names()
    if not container_names:
        return None
    next_server = container_names[count % len(container_names)]
    count += 1
    return next_server

class TaskManager:
    _lock = threading.Lock()
    _instance = None

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TaskManager, cls).__new__(cls)
                cls._instance.worker_states = {f"worker_{i+1}": "inactive" for i in range(5)}
                cls._instance.last_active_times = {f"worker_{i+1}": time.time() for i in range(5)}
                cls._instance.request_history = collections.defaultdict(lambda: collections.deque(maxlen=5))
                cls._instance.task_queue = queue.Queue()
                cls._instance.client = docker.from_env()
                cls._instance.base_port = 5001
                cls._instance.limit_try = 0
                cls._instance.successful_task = 0
                cls._instance.task_list_duplicate = []
                cls._instance.task_list = []
                cls._instance._initialize_workers()
                cls._instance._initialize_status_checker()
                cls._instance._initialize_idle_checker()  # Initialize the idle checker
        return cls._instance

    def _initialize_workers(self):
        for _ in range(3):  # Creating three worker threads for improved concurrency
            thread = threading.Thread(target=self._process_tasks)
            thread.daemon = True
            thread.start()

    def _initialize_status_checker(self):
        status_checker_thread = threading.Thread(target=self._check_worker_status)
        status_checker_thread.daemon = True
        status_checker_thread.start()

    def _initialize_idle_checker(self):
        idle_checker_thread = threading.Thread(target=self._check_idle_workers)
        idle_checker_thread.daemon = True
        idle_checker_thread.start()

    def _check_worker_status(self):
        while True:
            app.logger.info("Checking worker status...")
            # List to track active workers
            active_workers = [w for w, state in self.worker_states.items() if state == 'active']
            #app.logger.info(f"Active workers: {active_workers}, Last active times: {self.last_active_times[active_workers[0]]}")
            # If there are no active workers and the total count of workers is less than 5
            if not active_workers and len(get_running_container_names()) < 5:
                app.logger.info("No active workers found. Attempting to create new worker.")
                name = len(get_running_container_names()) + 1
                self.create_workers(1, name)
                app.logger.info(f"All workers are inactive. Attempting to create new worker: worker_{name}")

            # Additionally, handle scenario where all workers are inactive but the max limit hasn't been reached
            elif all(state != 'active' for state in self.worker_states.values()) and len(self.worker_states) < 5:
                name = len(self.worker_states) + 1
                self.create_workers(1, name)
                app.logger.info(f"All workers are inactive but not at max capacity. Creating new worker: worker_{name}")

            time.sleep(2)  # Adjusted to 10 seconds for better system performance

    def _process_tasks(self):
        while True:
            try:
                task_data = self.task_queue.get(timeout=5)  # Adjust timeout to reduce load
                if not self.assign_task(task_data):
                    time.sleep(1)  # Adding delay before re-queuing
                    self.task_queue.put(task_data)
            except queue.Empty:
                continue

    def _check_idle_workers(self):
        idle_limit = 60  # Idle time limit in seconds
        while True:
            current_time = time.time()
            running_containers = get_running_container_names()  # Get currently running container names
            with self._lock:
                for worker, last_active in list(self.last_active_times.items()):
                    if (current_time - last_active > idle_limit and
                        worker in running_containers):  # Ensure worker is still running
                        self.delete_worker(worker)
                time.sleep(1)

    def delete_worker(self, worker):
        try:
            container = self.client.containers.get(worker)
            container.stop()
            container.remove()
            app.logger.info(f"Deleted idle worker: {worker}")
            self.worker_states.pop(worker, None)
            # Do not clear history here, allowing it to persist
        except docker.errors.NotFound:
            app.logger.warning(f"Worker {worker} not found for deletion.")
        except Exception as e:
            app.logger.error(f"Error deleting worker {worker}: {e}")

    def assign_task(self, task_data):
        for worker_id, state in self.worker_states.items():
            if state == 'active':
                if self.send_task(task_data, worker_id):
                    return True
        return False

    def send_task(self, task_data, worker):
        url = f'http://{worker}:8110/receive_data'
        try:
            response = requests.post(url, json=task_data, timeout=5)
            if response.status_code == 200 and response.json().get('received'):
                self.successful_task += 1
                socketio.emit('task_completed')
                self.request_history[worker].append(task_data)  # Storing without the time to simplify the example
                self.last_active_times[worker] = time.time()
                return True
            else:
                self.update_worker_state(worker, 'inactive')
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Error sending task to {worker}: {e}")
            self.update_worker_state(worker, 'error')
        return False

    def update_worker_state(self, worker_id, state):
        self.worker_states[worker_id] = state

    def get_worker_state(self, worker_id):
        return self.worker_states.get(worker_id, "unknown")

    def load_task(self, data):
        self.task_queue.put(data)
        self.task_list_duplicate.append(data)

    def create_workers(self, num_workers, name=None):
        with self._lock:
            current_workers = get_running_container_names()
            if len(current_workers) >= 5:
                app.logger.info("Maximum number of workers reached. No more workers will be created.")
                return {}

            workers = {}
            for i in range(num_workers):
                if name:
                    container_name = f"worker_{name}"
                    port = self.base_port + len(current_workers) + i  # Adjusted port assignment
                else:
                    container_name = f"worker_{i+ 1}"
                    port = self.base_port  + i

                # Check if the container already exists and is running
                if container_name in current_workers:
                    app.logger.info(f"Worker {container_name} already exists and is running. Skipping creation.")
                    self.worker_states[container_name] = "active"  # Update the state if necessary
                    continue
                app.logger.info(f"Creating worker {container_name}")
                try:
                    container = self.client.containers.run(
                        "worker_image",
                        detach=True,
                        ports={'8110/tcp': port},
                        environment={'NODE_ID': f'node_{len(current_workers) + i + 1}', 'PORT': '8110'},
                        name=container_name,
                        hostname=container_name,
                        network='abc-net',
                        labels={'com.docker.compose.project': "distributedsessionnet"}
                    )
                    workers[container_name] = f'http://localhost:{port}'
                    app.logger.info(f"Worker {container_name} created successfully.")
                    time.sleep(1)  # Wait for the worker to start
                    self.worker_states[container_name] = "active"
                    current_workers.append(container_name)
                except docker.errors.APIError as e:
                    app.logger.error(f"Failed to create worker {container_name}: {e}")

            return workers

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
