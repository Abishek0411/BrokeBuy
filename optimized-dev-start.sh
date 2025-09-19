#!/bin/bash

# Optimized development startup script
# This script starts services only when needed and runs BrokeBuy

echo "🚀 Starting BrokeBuy Development Environment (Optimized)..."

# Start required system services first
echo "🔧 Starting system services..."
./start-services.sh

if [ $? -ne 0 ]; then
    echo "❌ Failed to start system services"
    exit 1
fi

# Wait a moment for services to be ready
sleep 3

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
    (cd "$dir" && $cmd) &
    local pid=$!
    echo "$name started with PID: $pid"
    echo $pid > ".${name,,}.pid"
}

# Start Backend (FastAPI) - using dedicated script
echo "🔄 Starting Backend..."
./start-backend.sh

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 5

# Start Scraper (Node.js)
start_service "Scraper" "npm start" "/home/abishek/Downloads/SRM-Academia-Scraper-node-main/server"

# Wait for scraper to start
echo "⏳ Waiting for scraper to start..."
sleep 3

# Start Frontend (React)
start_service "Frontend" "npm run dev" "/home/abishek/Downloads/proj_BrokeBuy_frontend/srm-brokebuy-vibe"

# Wait for frontend to start
echo "⏳ Waiting for frontend to start..."
sleep 3

# Verify all services are running
echo ""
echo "🔍 Verifying services..."

# Check backend
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend: Running"
else
    echo "❌ Backend: Not responding"
fi

# Check scraper
if curl -s http://localhost:3001/health > /dev/null 2>&1; then
    echo "✅ Scraper: Running"
else
    echo "❌ Scraper: Not responding"
fi

# Check frontend
if curl -s http://localhost:5173/ > /dev/null 2>&1; then
    echo "✅ Frontend: Running"
else
    echo "❌ Frontend: Not responding"
fi

echo ""
echo "🎉 All services started!"
echo ""
echo "📱 Services running:"
echo "   Backend API:    http://localhost:8000"
echo "   API Docs:       http://localhost:8000/docs"
echo "   Scraper:        http://localhost:3001"
echo "   Frontend:       http://localhost:5173"
echo ""
echo "🛑 To stop all services, run: ./optimized-dev-stop.sh"
echo "📊 To view logs, run: ./dev-logs.sh"
echo "💾 To stop system services and save resources, run: ./stop-services.sh"
