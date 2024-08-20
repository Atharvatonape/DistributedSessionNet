import docker

# Initialize the Docker client
client = docker.from_env()

def get_running_container_names():
    # Retrieve a list of all running containers
    containers = client.containers.list(all=False)  # all=False is default and could be omitted for brevity
    # Extract and return the names of these containers
    container_names = [container.name for container in containers]
    return container_names

# Print the names of all currently running containers
print(get_running_container_names())
