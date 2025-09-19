#!/bin/bash

# Optimized development stop script
# This script stops all BrokeBuy services and optionally system services

echo "🛑 Stopping BrokeBuy Development Environment..."

# Function to stop service by PID file
stop_service() {
    local name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "🔄 Stopping $name (PID: $pid)..."
            kill "$pid"
            rm -f "$pid_file"
            echo "✅ $name stopped"
        else
            echo "⚠️  $name was not running"
            rm -f "$pid_file"
        fi
    else
        echo "⚠️  No PID file found for $name"
    fi
}

# Stop all application services
stop_service "Backend" "/home/abishek/Downloads/proj_BrokeBuy_backend/.backend.pid"
stop_service "Scraper" "/home/abishek/Downloads/SRM-Academia-Scraper-node-main/server/.scraper.pid"
stop_service "Frontend" "/home/abishek/Downloads/proj_BrokeBuy_frontend/srm-brokebuy-vibe/.frontend.pid"

# Kill any remaining processes on our ports
echo "🧹 Cleaning up any remaining processes..."
lsof -ti:8000 | xargs -r kill -9 2>/dev/null
lsof -ti:3001 | xargs -r kill -9 2>/dev/null
lsof -ti:5173 | xargs -r kill -9 2>/dev/null

echo "✅ All application services stopped!"

# Ask if user wants to stop system services to save resources
echo ""
read -p "💾 Do you want to stop MongoDB and Docker to save resources? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔄 Stopping system services..."
    ./stop-services.sh
else
    echo "ℹ️  MongoDB and Docker are still running. Run ./stop-services.sh later to save resources."
fi
