#!/bin/bash

# Build and run Reading List Frontend with Docker

echo "🐳 Building Reading List Frontend Docker image..."

# Build the Docker image
docker build -t reading-list-frontend .

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"

    echo "🚀 Starting container..."
    docker run -d \
        --name reading-list-frontend \
        -p 3000:80 \
        -e REACT_APP_API_URL=http://localhost:8000 \
        reading-list-frontend

    if [ $? -eq 0 ]; then
        echo "✅ Container started successfully!"
        echo "🌐 Frontend is available at: http://localhost:3000"
        echo "📊 Container status:"
        docker ps | grep reading-list-frontend
    else
        echo "❌ Failed to start container"
        exit 1
    fi
else
    echo "❌ Failed to build Docker image"
    exit 1
fi
