import docker

client = docker.from_env()

def get_container_ips_by_name_prefix(name_prefix, network_name):
    # List all containers
    containers = client.containers.list(all=True)  # `all=True` includes stopped containers if needed
    container_ips = []
    for container in containers:
        # Check if the container's name starts with the name prefix
        if container.name.startswith(name_prefix):
            # Check if the specified network is available in the container's network settings
            networks = container.attrs['NetworkSettings']['Networks']
            if network_name in networks:
                ip_address = networks[network_name]['IPAddress']
                container_ips.append((container.name, ip_address))  # Collecting both name and IP for clarity
            else:
                print(f"Warning: The network '{network_name}' is not attached to the container '{container.name}'.")
    if not container_ips:
        raise ValueError(f"No containers found with names starting with '{name_prefix}'.\n")
    return container_ips

# Replace 'session-net' with the actual name of the network if it's different
try:
    containers_info = get_container_ips_by_name_prefix('worker_', 'session-net')
    for name, ip in containers_info:
        print(f"Container: {name}, IP Address: {ip}")
except ValueError as e:
    print(e)
