#!/bin/bash

# Optimized service shutdown script
# This script stops BrokeBuy services to save resources

echo "🛑 Stopping BrokeBuy Services..."

# Function to stop service if running
stop_service_if_running() {
    local service=$1
    local name=$2
    
    if systemctl is-active --quiet $service; then
        echo "🔄 Stopping $name..."
        sudo systemctl stop $service
        sleep 1
        if ! systemctl is-active --quiet $service; then
            echo "✅ $name stopped successfully"
        else
            echo "⚠️  $name is still running"
        fi
    else
        echo "ℹ️  $name was not running"
    fi
}

# Stop Docker first (to stop any running containers)
stop_service_if_running "docker" "Docker"

# Stop MongoDB
stop_service_if_running "mongod" "MongoDB"

echo ""
echo "✅ All services stopped!"
echo "💾 Resources saved - MongoDB and Docker are no longer consuming RAM/CPU"
