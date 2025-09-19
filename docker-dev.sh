#!/bin/bash

# Docker development script for BrokeBuy project
# This script starts all services in development mode

echo "🐳 Starting BrokeBuy Development Environment with Docker..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start services in development mode
echo "🚀 Starting all services in development mode..."
docker-compose -f docker-compose.dev.yml up -d

echo ""
echo "🎉 All services started in development mode!"
echo ""
echo "📱 Services running:"
echo "   Backend API:    http://localhost:8000"
echo "   API Docs:       http://localhost:8000/docs"
echo "   Scraper:        http://localhost:3001"
echo "   Frontend:       http://localhost:5173"
echo "   MongoDB:        localhost:27017"
echo ""
echo "🛑 To stop all services, run: ./docker-stop-dev.sh"
echo "📊 To view logs, run: ./docker-logs-dev.sh"
