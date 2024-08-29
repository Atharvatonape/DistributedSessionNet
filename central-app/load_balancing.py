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

def round_robin():
    global count
    container_names = get_running_container_names()
    next_server = container_names[count]
    count = (count + 1)
    if count >= len(container_names):
        count = 0
    return next_server

class TaskManager:
    _lock = Lock()
    _instance = None

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TaskManager, cls).__new__(cls)
                cls._instance.worker_states = {"worker_1": "inactive", "worker_2": "inactive", "worker_3": "inactive", "worker_4": "inactive", "worker_5": "inactive"}
                cls._instance.task_list = []
                cls._instance.taske = []
                cls._instance.client = docker.from_env()
                cls._instance.base_port = 5001
                cls._instance.limit_try = 0
                cls._instance._initialize_worker_thread()
                cls._instance._initialize_status_checker()
        return cls._instance

    def _initialize_worker_thread(self):
        self._worker_thread = Thread(target=self._process_tasks)
        self._worker_thread.daemon = True
        self._worker_thread.start()

    def _initialize_status_checker(self):
        self._status_checker_thread = Thread(target=self._check_worker_status)
        self._status_checker_thread.daemon = True
        self._status_checker_thread.start()

    def _check_worker_status(self):
        while True:
            all_inactive = True  # Assume all are inactive until we find an active one
            for worker_id in get_running_container_names():
                self._get_worker_status(worker_id)
                if self.get_worker_state(worker_id) == 'active':
                    all_inactive = False

            if all_inactive:
                app.logger.info("All workers are inactive.")
                if self.limit_try < 5:
                    self.limit_try += 1
                    app.logger.info(f"Creating new worker attempt {self.limit_try}")
                    name = len(get_running_container_names()) + 1
                    app.logger.info(f"Creating new worker with name: {name}")
                    self.create_workers(1, name )  # Create one more worker
                else:
                    app.logger.info("Max retry limit reached. No more workers will be created.")
            time.sleep(5)

    def _get_worker_status(self, worker_id):
        #app.logger.info(f"Checking status of {worker_id}")
        url = f'http://{worker_id}:8110/status'  # assuming worker URL includes its ID and listens on port 8110
        try:
            response = requests.get(url)
            if response.status_code == 200:
                status_info = response.json()
                active = status_info['active']
                print(f"Status of {worker_id} is active: {active}")
                self.update_worker_state(worker_id, 'active' if active else 'inactive')
                #app.logger.info(f"Status of {worker_id} is : {active}")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching status for {worker_id}: {str(e)}")
            self.update_worker_state(worker_id, 'error')

    def _process_tasks(self):
        """ Continuously process and assign tasks to available workers. """
        while True:
            available_workers = [w for w, state in self.worker_states.items() if state == 'active']
            app.logger.info(f"Available workers: {available_workers}")
            while self.task_list and available_workers:  # Check if task list is not empty
                task_data = self.task_list.pop(0)  # Retrieve a task from the front of the list
                worker = available_workers.pop(0)  # Use round-robin to select the next available worker
                self.send_task(task_data, worker)
                available_workers.append(worker)  # Add worker back to the end of the list

            time.sleep(1)

    def send_task(self, task_data, worker):
        #app.logger.info(f"Sending task: {task_data}")
        if self.get_worker_state(worker) == "active":
            response = requests.post(f'http://{worker}:8110/receive_data', json=task_data)
            if response.status_code != 200:
                #app.logger.info(f"Failed to send task to {worker}. Status code: {response.status_code}")
                self.task_list.append(task_data)
            else:
                app.logger.info(f"Task sent successfully to {worker}.")

    def update_worker_state(self, worker_id, state):
        self.worker_states[worker_id] = state

    def get_worker_state(self, worker_id):
        return self.worker_states.get(worker_id, "unknown")

    def load_task(self, data):
        self.taske.append(data)
        app.logger.info(f"Task loaded: {len(self.taske)}")
        self.task_list.append(data)
        app.logger.info(f"Task list: {len(self.task_list)}")

    def create_workers(self, num_workers, name=None):
        with self._lock:  # Ensure only one thread can enter this block at a time
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
                    continue  # Skip to the next iteration

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
                    self.worker_states[container_name] = "active"
                    current_workers.append(container_name)  # Add the new container name to the list
                except docker.errors.APIError as e:
                    app.logger.error(f"Failed to create worker {container_name}: {e}")

            return workers



    def _stop_and_remove_container(self, container_name):
        try:
            existing_container = self.client.containers.get(container_name)
            existing_container.stop()
            existing_container.remove()
        except docker.errors.NotFound:
            pass