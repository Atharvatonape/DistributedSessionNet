import docker

def get_worker_ip_map():
    client = docker.from_env()
    containers = client.containers.list(filters={"label": "com.docker.compose.project=distributedsessionnet"})
    worker_ip_map = {}

    for container in containers:
        container_name = container.name
        # Skip the central application container
        if "central" not in container_name:
            container_details = container.attrs
            ip_address = container_details['NetworkSettings']['Networks']['abc-net']['IPAddress']
            worker_ip_map[container_name] = ip_address

    return worker_ip_map

# Example usage:
worker_ips = get_worker_ip_map()
print(worker_ips)

