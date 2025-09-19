#!/bin/bash

# BrokeBuy Server Management Script
# This script helps manage the BrokeBuy application on the production server

set -e

# Configuration
SERVER_USER="srmadmin"
SERVER_HOST="172.16.0.60"
SERVER_PASSWORD="SRM_Admin"
SERVER_PATH="/home/srmadmin/brokebuy"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "BrokeBuy Server Management Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  status      - Show service status"
    echo "  logs        - Show service logs"
    echo "  restart     - Restart all services"
    echo "  stop        - Stop all services"
    echo "  start       - Start all services"
    echo "  update      - Update and restart services"
    echo "  backup      - Backup database"
    echo "  restore     - Restore database from backup"
    echo "  monitor     - Monitor resource usage"
    echo "  shell       - Open shell on server"
    echo ""
}

# Check service status
check_status() {
    print_status "Checking service status..."
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST "cd $SERVER_PATH && docker-compose -f docker-compose.prod.yml ps"
}

# Show logs
show_logs() {
    local service=${1:-""}
    if [ -n "$service" ]; then
        print_status "Showing logs for $service..."
        sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST "cd $SERVER_PATH && docker-compose -f docker-compose.prod.yml logs -f $service"
    else
        print_status "Showing logs for all services..."
        sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST "cd $SERVER_PATH && docker-compose -f docker-compose.prod.yml logs -f"
    fi
}

# Restart services
restart_services() {
    print_status "Restarting services..."
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST "cd $SERVER_PATH && docker-compose -f docker-compose.prod.yml restart"
    print_success "Services restarted"
}

# Stop services
stop_services() {
    print_status "Stopping services..."
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST "cd $SERVER_PATH && docker-compose -f docker-compose.prod.yml down"
    print_success "Services stopped"
}

# Start services
start_services() {
    print_status "Starting services..."
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST "cd $SERVER_PATH && docker-compose -f docker-compose.prod.yml up -d"
    print_success "Services started"
}

# Update services
update_services() {
    print_status "Updating services..."
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST << 'EOF'
        cd /home/srmadmin/brokebuy
        
        # Pull latest changes (if using git)
        # git pull origin main
        
        # Rebuild and restart services
        docker-compose -f docker-compose.prod.yml down
        docker-compose -f docker-compose.prod.yml up -d --build
        
        # Clean up old images
        docker image prune -f
        
        echo "Services updated successfully"
EOF
    print_success "Services updated"
}

# Backup database
backup_database() {
    local backup_file="brokebuy_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    print_status "Creating database backup: $backup_file"
    
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST << EOF
        cd $SERVER_PATH
        
        # Create backup directory if it doesn't exist
        mkdir -p backups
        
        # Create database backup
        docker exec brokebuy-mongodb-prod mongodump --out /tmp/backup
        docker cp brokebuy-mongodb-prod:/tmp/backup ./backups/$backup_file
        docker exec brokebuy-mongodb-prod rm -rf /tmp/backup
        
        echo "Backup created: backups/$backup_file"
EOF
    
    print_success "Database backup created: $backup_file"
}

# Restore database
restore_database() {
    local backup_file=$1
    if [ -z "$backup_file" ]; then
        print_error "Please provide backup file name"
        echo "Available backups:"
        sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST "cd $SERVER_PATH && ls -la backups/ 2>/dev/null || echo 'No backups found'"
        exit 1
    fi
    
    print_warning "This will replace the current database. Are you sure? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        print_status "Restore cancelled"
        exit 0
    fi
    
    print_status "Restoring database from $backup_file..."
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST << EOF
        cd $SERVER_PATH
        
        # Stop services
        docker-compose -f docker-compose.prod.yml down
        
        # Remove current data
        docker volume rm brokebuy_mongodb_data || true
        
        # Start MongoDB only
        docker-compose -f docker-compose.prod.yml up -d mongodb
        
        # Wait for MongoDB to be ready
        sleep 10
        
        # Restore database
        docker cp ./backups/$backup_file brokebuy-mongodb-prod:/tmp/backup.tar.gz
        docker exec brokebuy-mongodb-prod tar -xzf /tmp/backup.tar.gz -C /tmp/
        docker exec brokebuy-mongodb-prod mongorestore /tmp/backup
        
        # Start all services
        docker-compose -f docker-compose.prod.yml up -d
        
        echo "Database restored from $backup_file"
EOF
    
    print_success "Database restored from $backup_file"
}

# Monitor resource usage
monitor_resources() {
    print_status "Monitoring resource usage..."
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST << 'EOF'
        echo "=== Docker Container Stats ==="
        docker stats --no-stream
        
        echo ""
        echo "=== System Resources ==="
        echo "Memory Usage:"
        free -h
        
        echo ""
        echo "Disk Usage:"
        df -h
        
        echo ""
        echo "CPU Usage:"
        top -bn1 | grep "Cpu(s)"
EOF
}

# Open shell on server
open_shell() {
    print_status "Opening shell on server..."
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST
}

# Main function
main() {
    case "${1:-}" in
        "status")
            check_status
            ;;
        "logs")
            show_logs "$2"
            ;;
        "restart")
            restart_services
            ;;
        "stop")
            stop_services
            ;;
        "start")
            start_services
            ;;
        "update")
            update_services
            ;;
        "backup")
            backup_database
            ;;
        "restore")
            restore_database "$2"
            ;;
        "monitor")
            monitor_resources
            ;;
        "shell")
            open_shell
            ;;
        *)
            show_usage
            ;;
    esac
}

# Run main function
main "$@"
