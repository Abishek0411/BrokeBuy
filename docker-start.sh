#!/bin/bash

# Docker startup script for BrokeBuy project
# This script starts all services using Docker Compose

echo "🐳 Starting BrokeBuy with Docker..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Start services
echo "🚀 Starting all services..."
docker-compose up -d

echo ""
echo "🎉 All services started!"
echo ""
echo "📱 Services running:"
echo "   Backend API:    http://localhost:8000"
echo "   API Docs:       http://localhost:8000/docs"
echo "   Scraper:        http://localhost:3001"
echo "   Frontend:       http://localhost:80"
echo "   MongoDB:        localhost:27017"
echo ""
echo "🛑 To stop all services, run: ./docker-stop.sh"
echo "📊 To view logs, run: ./docker-logs.sh"
echo "🔧 For development mode, run: ./docker-dev.sh"
