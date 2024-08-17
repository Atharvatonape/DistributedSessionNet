#!/bin/bash

# Stop and remove all existing containers, networks, and volumes
# The `--volumes` option ensures that volumes are also removed, and `--rmi all` removes all images

echo "Stopping and removing all containers, networks, and volumes..."

docker-compose down --volumes --remove-orphans --rmi all

# Add a check for successful operation
if [ $? -eq 0 ]; then
    echo "All containers, networks, volumes, and images have been removed successfully."
else
    echo "Failed to stop and remove containers, networks, and volumes."
fi
