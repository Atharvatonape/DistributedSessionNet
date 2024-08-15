#!/bin/bash

# Stop and remove all existing containers, networks, and volumes
docker-compose down

# Build new images and start the containers
docker-compose up --build -d