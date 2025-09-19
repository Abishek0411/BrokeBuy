#!/bin/bash

# Docker stop script for BrokeBuy project
# This script stops all services

echo "🛑 Stopping BrokeBuy Docker services..."

# Stop all services
docker-compose down

echo "✅ All services stopped!"
