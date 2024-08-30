from utils.docker_containers import get_running_container_names
import requests
from utils.fake_data import fake_data_gen
from threading import Lock, Thread
import queue
import threading
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import time
import docker
import logging

count = 0
app = Flask(__name__)
app.logger.setLevel(logging.INFO)
socketio = SocketIO(app)

def round_robin():
    global count
    container_names = get_running_container_names()
    next_server = container_names[count]
    count = (count + 1)
    if count >= len(container_names):
        count = 0
    return next_server

class TaskManager:
    _lock = threading.Lock()
    _instance = None

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TaskManager, cls).__new__(cls)
                cls._instance.worker_states = {"worker_1": "inactive", "worker_2": "inactive", "worker_3": "inactive", "worker_4": "inactive", "worker_5": "inactive"}
                cls._instance.task_queue = queue.Queue()
                cls._instance.client = docker.from_env()
                cls._instance.base_port = 5001
                cls._instance.limit_try = 0
                cls._instance.successful_task = 0
                cls._instance.task_list_duplicate = []
                cls._instance.task_list = []
                cls._instance._initialize_worker_thread()
                cls._instance._initialize_status_checker()
        return cls._instance

    def _initialize_worker_thread(self):
        self._worker_thread = threading.Thread(target=self._process_tasks)
        self._worker_thread.daemon = True
        self._worker_thread.start()

    def _initialize_status_checker(self):
        self._status_checker_thread = threading.Thread(target=self._check_worker_status)
        self._status_checker_thread.daemon = True
        self._status_checker_thread.start()

    def _check_worker_status(self):
        while True:
            all_inactive = True
            app.logger.info("Checking worker status...")
            for worker_id in get_running_container_names():
                self._get_worker_status(worker_id)
                if self.get_worker_state(worker_id) == 'active':
                    app.logger.info(f"Worker {worker_id} is active.") # Log active workers
                    all_inactive = False

            if all_inactive:
                app.logger.info("All workers are inactive.")
                if self.limit_try < 5:
                    self.limit_try += 1
                    app.logger.info(f"Creating new worker attempt {self.limit_try}")
                    name = len(get_running_container_names()) + 1
                    app.logger.info(f"Creating new worker with name: {name}")
                    self.create_workers(1, name)
                    #requests.get('http://localhost:5000/workers_get')
                else:
                    app.logger.info("Max retry limit reached. No more workers will be created.")
            time.sleep(5)

    def _get_worker_status(self, worker_id):
        url = f'http://{worker_id}:8110/status'
        try:
            response = requests.get(url)
            if response.status_code == 200:
                status_info = response.json()
                active = status_info['active']
                self.update_worker_state(worker_id, 'active' if active else 'inactive')
        except requests.exceptions.RequestException as e:
            print(f"Error fetching status for {worker_id}: {str(e)}")
            self.update_worker_state(worker_id, 'error')

    def _process_tasks(self):
        while True:
            try:
                task_data = self.task_queue.get(timeout=1)  # Attempt to get a task, waits for 1 second
                if not self.assign_task(task_data):
                    self.task_queue.put(task_data)  # Requeue task if assignment fails
            except queue.Empty:
                continue  # Continue if no tasks are available

    def assign_task(self, task_data):
        for worker_id, state in self.worker_states.items():
            if state == 'active':
                if self.send_task(task_data, worker_id):
                    return True  # Task successfully sent, do not requeue
        return False  # Task not sent, needs requeuing

    def send_task(self, task_data, worker):
        url = f'http://{worker}:8110/receive_data'
        try:
            response = requests.post(url, json=task_data, timeout=5)
            if response.status_code == 200:
                #app.logger.info(f"Task sent successfully to {worker}.")
                self.successful_task += 1
                socketio.emit('task_completed')
                #requests.get('http://localhost:5000/workers_get')  # Retrieve worker stats after sending a task
                return True
            else:
                app.logger.warning(f"Failed to send task to {worker}, status code {response.status_code}.")
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Error sending task to {worker}: {e}")
        return False

    def update_worker_state(self, worker_id, state):
        self.worker_states[worker_id] = state
        #app.logger.info(f"Worker state updated: {worker_id} - {state}")

    def get_worker_state(self, worker_id):
        return self.worker_states.get(worker_id, "unknown")

    def load_task(self, data):
        self.task_queue.put(data)
        #app.logger.info(f"Task loaded: {self.task_queue.qsize()}")
        self.task_list_duplicate.append(data)
        self.task_list.append(data)

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
                    time.sleep(5)  # Wait for the worker to start
                    self.worker_states[container_name] = "active"
                    current_workers.append(container_name)
                except docker.errors.APIError as e:
                    app.logger.error(f"Failed to create worker {container_name}: {e}")

            return workers