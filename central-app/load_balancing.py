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
            for worker_id in list(self.worker_states.keys()):
                self._get_worker_status(worker_id)
            time.sleep(5)  # Pause for 10 seconds before the next status check

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
                app.logger.info(f"Status of {worker_id} is active: {active}")
            else:
                print(f"Failed to get status from {worker_id}. Status code: {response.status_code}")
                self.update_worker_state(worker_id, 'error')
        except requests.exceptions.RequestException as e:
            print(f"Error fetching status for {worker_id}: {str(e)}")
            self.update_worker_state(worker_id, 'error')

    def _process_tasks(self):
        while True:
            if any(state == "active" for state in self.worker_states.values()):
                if self.task_list:
                    task_data = self.task_list.pop(0)
                    self.send_task(task_data)
            else:
                time.sleep(2)

    def send_task(self, task_data):
        worker = round_robin()  # Placeholder for actual round-robin function
        if self.get_worker_state(worker) == "active":
            response = requests.post(f'http://{worker}:8110/receive_data', json=task_data)
            if response.status_code != 200:
                print(f"Failed to send task to {worker}. Status code: {response.status_code}")
                self.task_list.append(task_data)
            else:
                print(f"Task sent successfully to {worker}.")
        else:
            print(f"Worker {worker} is not active. Task not sent.")
            self.task_list.append(task_data)

    def update_worker_state(self, worker_id, state):
        self.worker_states[worker_id] = state

    def get_worker_state(self, worker_id):
        return self.worker_states.get(worker_id, "unknown")

    def load_task(self, data):
        self.taske.append(data)
        app.logger.info(f"Task loaded: {len(self.taske)}")
        self.task_list.append(data)
        app.logger.info(f"Task list: {len(self.task_list)}")

    def create_workers(self, num_workers):
        workers = {}
        worker_names = get_running_container_names()
        for i in range(num_workers):
            container_name = f"worker_{i+1}"
            if container_name in worker_names:
                app.logger.info(f"Worker {container_name} already exists. Skipping...")
                continue
            app.logger.info(f"Creating worker {container_name}")
            port = self.base_port + i
            self._stop_and_remove_container(container_name)
            container = self.client.containers.run(
                "worker_image",
                detach=True,
                ports={'8110/tcp': port},
                environment={'NODE_ID': f'node_{i+1}', 'PORT': '8110'},
                name=container_name,
                hostname=container_name,
                network='abc-net',
                labels={'com.docker.compose.project': "session-management"}
            )
            workers[container_name] = f'http://localhost:{port}'
            self.worker_states[container_name] = "active"
        return workers

    def _stop_and_remove_container(self, container_name):
        try:
            existing_container = self.client.containers.get(container_name)
            existing_container.stop()
            existing_container.remove()
        except docker.errors.NotFound:
            pass