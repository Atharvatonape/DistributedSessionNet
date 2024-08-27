from utils.docker_containers import get_running_container_names
import requests
from utils.fake_data import fake_data_gen
from threading import Lock, Thread
import queue
import threading
import time


count = 0

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
                cls._instance._initialize_worker_thread()
        return cls._instance

    def _initialize_worker_thread(self):
        self._worker_thread = Thread(target=self._process_tasks)
        self._worker_thread.daemon = True
        self._worker_thread.start()

    def _process_tasks(self):
        while True:
            # Check if at least one worker is active
            if any(state == "active" for state in self.worker_states.values()):
                if self.task_list:
                    task_data = self.task_list.pop(0)  # Remove the task from the beginning of the list
                    self.send_task(task_data)
            else:
                # Wait before rechecking the worker states to avoid busy waiting
                time.sleep(2)

    def send_task(self, task_data):
        worker = round_robin()  # Assuming this method selects the next worker in round-robin fashion
        if self.get_worker_state(worker) == "active":
            response = requests.post(f'http://{worker}:8110/receive_data', json=task_data)
            if response.status_code != 200:
                print(f"Failed to send task to {worker}. Status code: {response.status_code}")
                # Optionally, re-queue the failed task
                self.task_list.append(task_data)
            else:
                print(f"Task sent successfully to {worker}.")
        else:
            print(f"Worker {worker} is not active. Task not sent.")
            # Optionally, re-queue the task if the worker is not active
            self.task_list.append(task_data)

    def update_worker_state(self, worker_id, state):
        self.worker_states[worker_id] = state

    def get_worker_state(self, worker_id):
        return self.worker_states.get(worker_id, "unknown")

    def load_task(self, data):
        self.taske.append(data)
        self.task_list.append(data)