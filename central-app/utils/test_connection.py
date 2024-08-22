import requests

def check_worker_endpoints(worker_urls, timeout=5):
    statuses = {}
    for url in worker_urls:
        try:
            response = requests.get(url, timeout=timeout)  # Sending a GET request to the worker endpoint
            if response.status_code == 200:
                statuses[url] = 'active'
            else:
                statuses[url] = f'inactive (status code: {response.status_code})'
        except requests.exceptions.RequestException as e:
            statuses[url] = f'inactive (error: {str(e)})'
    return statuses

# Example URLs of worker endpoints
worker_urls = [
    'http://localhost:5001',
    "http://localhost:5002",
    "http://localhost:5003"
]

# Checking the status of each worker
worker_statuses = check_worker_endpoints(worker_urls)
for url, status in worker_statuses.items():
    print(f"Endpoint: {url}, Status: {status}")
