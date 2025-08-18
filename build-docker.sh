#!/bin/bash

# Script to build the LmyDigitalHuman Docker image with the fixed Program.cs

echo "Building LmyDigitalHuman Docker image..."
echo "========================================="

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "Error: docker-compose.yml not found in current directory"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed or not in PATH"
    exit 1
fi

# Check if Docker Compose is available
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "Error: Docker Compose is not installed"
    exit 1
fi

# Build the image
echo "Using command: $COMPOSE_CMD"
echo "Building with no-cache option..."

$COMPOSE_CMD -f docker-compose.yml -f docker-compose.local.yml build --no-cache lmy-digitalhuman

if [ $? -eq 0 ]; then
    echo "========================================="
    echo "Build completed successfully!"
else
    echo "========================================="
    echo "Build failed. Please check the error messages above."
    exit 1
fi