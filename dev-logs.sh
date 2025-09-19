#!/bin/bash

# Development logs script for BrokeBuy project
# This script shows logs for all services

echo "📊 BrokeBuy Development Logs"
echo "=============================="
echo ""

# Function to show logs for a service
show_logs() {
    local name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "📱 $name Logs (PID: $pid):"
            echo "------------------------"
            # Note: This is a simple implementation. In production, you'd want proper log files
            echo "Service is running. Check terminal output for logs."
            echo ""
        else
            echo "⚠️  $name is not running"
            echo ""
        fi
    else
        echo "⚠️  $name is not running"
        echo ""
    fi
}

show_logs "Backend" "/home/abishek/Downloads/proj_BrokeBuy_backend/.backend.pid"
show_logs "Scraper" "/home/abishek/Downloads/SRM-Academia-Scraper-node-main/server/.scraper.pid"
show_logs "Frontend" "/home/abishek/Downloads/proj_BrokeBuy_frontend/srm-brokebuy-vibe/.frontend.pid"

echo "💡 Tip: Run each service in separate terminals to see individual logs:"
echo "   Backend:  cd /home/abishek/Downloads/proj_BrokeBuy_backend && source myenv/bin/activate && uvicorn app.main:app --reload"
echo "   Scraper:  cd /home/abishek/Downloads/SRM-Academia-Scraper-node-main/server && npm start"
echo "   Frontend: cd /home/abishek/Downloads/proj_BrokeBuy_frontend/srm-brokebuy-vibe && npm run dev"
