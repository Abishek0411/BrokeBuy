#!/bin/bash

# Docker development logs script for BrokeBuy project
# This script shows logs for all development services

echo "📊 BrokeBuy Development Docker Logs"
echo "===================================="
echo ""

# Show logs for all development services
docker-compose -f docker-compose.dev.yml logs -f
