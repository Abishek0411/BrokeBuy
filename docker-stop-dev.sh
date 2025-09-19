#!/bin/bash

# Docker development stop script for BrokeBuy project
# This script stops all development services

echo "🛑 Stopping BrokeBuy Development Docker services..."

# Stop all development services
docker-compose -f docker-compose.dev.yml down

echo "✅ All development services stopped!"
