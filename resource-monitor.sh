#!/bin/bash

# Resource monitoring script for BrokeBuy services
# This script shows current resource usage

echo "📊 BrokeBuy Resource Monitor"
echo "============================"
echo ""

# System resources
echo "🖥️  System Resources:"
echo "--------------------"
free -h
echo ""

# CPU usage
echo "⚡ CPU Usage:"
echo "------------"
top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print "CPU Usage: " 100 - $1 "%"}'
echo ""

# MongoDB status and resources
echo "🗄️  MongoDB Status:"
echo "------------------"
if systemctl is-active --quiet mongod; then
    echo "Status: ✅ Running"
    echo "Memory: $(ps aux | grep mongod | grep -v grep | awk '{print $6/1024 " MB"}')"
    echo "CPU: $(ps aux | grep mongod | grep -v grep | awk '{print $3 "%"}')"
else
    echo "Status: ❌ Stopped"
fi
echo ""

# Docker status and resources
echo "🐳 Docker Status:"
echo "----------------"
if systemctl is-active --quiet docker; then
    echo "Status: ✅ Running"
    echo "Memory: $(ps aux | grep dockerd | grep -v grep | awk '{print $6/1024 " MB"}')"
    echo "CPU: $(ps aux | grep dockerd | grep -v grep | awk '{print $3 "%"}')"
    echo ""
    echo "Docker Resources:"
    sudo docker system df 2>/dev/null || echo "Docker not accessible"
else
    echo "Status: ❌ Stopped"
fi
echo ""

# Application services
echo "🚀 Application Services:"
echo "-----------------------"
for service in "Backend" "Scraper" "Frontend"; do
    case $service in
        "Backend")
            if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null; then
                echo "$service: ✅ Running (Port 8000)"
            else
                echo "$service: ❌ Stopped"
            fi
            ;;
        "Scraper")
            if lsof -Pi :3001 -sTCP:LISTEN -t >/dev/null; then
                echo "$service: ✅ Running (Port 3001)"
            else
                echo "$service: ❌ Stopped"
            fi
            ;;
        "Frontend")
            if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null; then
                echo "$service: ✅ Running (Port 5173)"
            else
                echo "$service: ❌ Stopped"
            fi
            ;;
    esac
done

echo ""
echo "💡 Resource Saving Tips:"
echo "-----------------------"
echo "• Run ./stop-services.sh to stop MongoDB and Docker when not needed"
echo "• Run ./docker-cleanup.sh to clean up Docker resources"
echo "• Use ./optimized-dev-start.sh for development (starts services only when needed)"
