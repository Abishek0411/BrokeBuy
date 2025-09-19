#!/bin/bash

# Optimized service startup script
# This script starts only the services needed for BrokeBuy

echo "🚀 Starting BrokeBuy Services..."

# Function to check if a service is running
is_service_running() {
    systemctl is-active --quiet $1
}

# Function to start service if not running
start_service_if_needed() {
    local service=$1
    local name=$2
    
    if is_service_running $service; then
        echo "✅ $name is already running"
    else
        echo "🔄 Starting $name..."
        sudo systemctl start $service
        sleep 2
        if is_service_running $service; then
            echo "✅ $name started successfully"
        else
            echo "❌ Failed to start $name"
            return 1
        fi
    fi
}

# Start MongoDB
start_service_if_needed "mongod" "MongoDB"

# Start Docker
start_service_if_needed "docker" "Docker"

echo ""
echo "🎉 All required services are running!"
echo "💡 Services will stop automatically when you run ./stop-services.sh"
