#!/bin/bash
set -e

echo "Building Docker image..."
docker build -t docflow .

echo "Starting container with hot reload (volume mount)..."
docker run -p 8501:8501 -v "$(pwd):/app" docflow