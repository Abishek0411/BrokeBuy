#!/bin/bash

# Docker logs script for BrokeBuy project
# This script shows logs for all services

echo "📊 BrokeBuy Docker Logs"
echo "======================="
echo ""

# Show logs for all services
docker-compose logs -f
