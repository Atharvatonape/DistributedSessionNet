import docker

# Initialize the Docker client
client = docker.from_env()

def get_running_container_names():
    # Retrieve a list of all running containers
    containers = client.containers.list(all=False)  # all=False is default and could be omitted for brevity
    # Extract and return the names of these containers
    container_names = []
    for container in containers:
        if "worker_" in container.name:
            container_names.append(container.name)
    return container_names

def get_urls_of_running_containers():
    """
    Retrieve URLs for all running Docker containers that have exposed ports.

    Returns:
    list: A list of strings containing the URLs of the containers.
    """
    client = docker.from_env()  # Create a Docker client using default configuration
    containers = client.containers.list()  # List only running containers
    urls = []

    # Iterate over each container and fetch URLs based on exposed ports
    for container in containers:
        ports = container.attrs['NetworkSettings']['Ports']
        for container_port, mappings in ports.items():
            if mappings is not None:
                for mapping in mappings:
                    # Assuming localhost; replace 'localhost' with your specific host if necessary
                    url = f"http://localhost:{mapping['HostPort']}"
                    if 'http://localhost:500' in url:
                        urls.append(url)

    return urls

# Print the names of all currently running containers
print(get_running_container_names())
print(get_urls_of_running_containers())