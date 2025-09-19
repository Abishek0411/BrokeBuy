#!/bin/bash

# Development startup script for BrokeBuy project
# This script starts all three services: Backend, Scraper, and Frontend

echo "🚀 Starting BrokeBuy Development Environment..."

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Port $1 is already in use. Please stop the service using this port first."
        return 1
    fi
    return 0
}

# Check if required ports are available
echo "🔍 Checking ports..."
check_port 8000 || exit 1  # Backend
check_port 3001 || exit 1  # Scraper
check_port 5173 || exit 1  # Frontend

# Function to start service in background
start_service() {
    local name=$1
    local cmd=$2
    local dir=$3
    
    echo "🔄 Starting $name..."
    cd "$dir" || exit 1
    $cmd &
    local pid=$!
    echo "$name started with PID: $pid"
    echo $pid > ".${name,,}.pid"
}

# Start MongoDB if not running
echo "🗄️  Checking MongoDB..."
if ! pgrep -x "mongod" > /dev/null; then
    echo "🔄 Starting MongoDB..."
    sudo systemctl start mongod
    sleep 2
fi

# Start Backend (FastAPI)
start_service "Backend" "source myenv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" "/home/abishek/Downloads/proj_BrokeBuy_backend"

# Start Scraper (Node.js)
start_service "Scraper" "npm start" "/home/abishek/Downloads/SRM-Academia-Scraper-node-main/server"

# Start Frontend (React)
start_service "Frontend" "npm run dev" "/home/abishek/Downloads/proj_BrokeBuy_frontend/srm-brokebuy-vibe"

echo ""
echo "🎉 All services started!"
echo ""
echo "📱 Services running:"
echo "   Backend API:    http://localhost:8000"
echo "   API Docs:       http://localhost:8000/docs"
echo "   Scraper:        http://localhost:3001"
echo "   Frontend:       http://localhost:5173"
echo ""
echo "🛑 To stop all services, run: ./dev-stop.sh"
echo "📊 To view logs, run: ./dev-logs.sh"
