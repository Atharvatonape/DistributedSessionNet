from utils.docker_containers import get_running_container_names

count = 0

def round_robin():
    global count
    container_names = get_running_container_names()
    next_server = container_names[count]
    count = (count + 1)
    if count >= len(container_names):
        count = 0
    return next_server
