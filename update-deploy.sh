#!/bin/bash

# BrokeBuy Update Deployment Script
# This script updates the production server with latest changes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVER_USER="srmadmin"
SERVER_HOST="172.16.0.60"
SERVER_PASSWORD="SRM_Admin"
SERVER_PATH="/home/srmadmin/brokebuy"
LOCAL_PATH="/home/abishek/Downloads"

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
    echo "BrokeBuy Update Deployment Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --backend-only    Update only backend"
    echo "  --frontend-only   Update only frontend"
    echo "  --scraper-only    Update only scraper"
    echo "  --all            Update all services (default)"
    echo "  --no-rebuild     Skip Docker rebuild (faster but may miss changes)"
    echo "  --help           Show this help message"
    echo ""
}

# Parse command line arguments
UPDATE_BACKEND=true
UPDATE_FRONTEND=true
UPDATE_SCRAPER=true
NO_REBUILD=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --backend-only)
            UPDATE_BACKEND=true
            UPDATE_FRONTEND=false
            UPDATE_SCRAPER=false
            shift
            ;;
        --frontend-only)
            UPDATE_BACKEND=false
            UPDATE_FRONTEND=true
            UPDATE_SCRAPER=false
            shift
            ;;
        --scraper-only)
            UPDATE_BACKEND=false
            UPDATE_FRONTEND=false
            UPDATE_SCRAPER=true
            shift
            ;;
        --all)
            UPDATE_BACKEND=true
            UPDATE_FRONTEND=true
            UPDATE_SCRAPER=true
            shift
            ;;
        --no-rebuild)
            NO_REBUILD=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Update backend
update_backend() {
    if [ "$UPDATE_BACKEND" = true ]; then
        print_status "Updating backend..."
        
        # Copy backend files
        sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no -r $LOCAL_PATH/proj_BrokeBuy_backend/* $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
        
        # Update backend on server
        sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST << EOF
            cd $SERVER_PATH
            
            # Stop backend container
            docker-compose -f docker-compose.prod.yml stop backend || true
            
            # Rebuild and start backend
            if [ "$NO_REBUILD" = true ]; then
                docker-compose -f docker-compose.prod.yml up -d backend
            else
                docker-compose -f docker-compose.prod.yml up -d --build backend
            fi
            
            echo "Backend updated"
EOF
        
        print_success "Backend updated"
    fi
}

# Update frontend
update_frontend() {
    if [ "$UPDATE_FRONTEND" = true ]; then
        print_status "Updating frontend..."
        
        # Copy frontend files
        sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no -r $LOCAL_PATH/proj_BrokeBuy_frontend/* $SERVER_USER@$SERVER_HOST:/home/srmadmin/proj_BrokeBuy_frontend/
        
        # Update frontend on server
        sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST << EOF
            cd $SERVER_PATH
            
            # Stop frontend container
            docker-compose -f docker-compose.prod.yml stop frontend || true
            
            # Rebuild and start frontend
            if [ "$NO_REBUILD" = true ]; then
                docker-compose -f docker-compose.prod.yml up -d frontend
            else
                docker-compose -f docker-compose.prod.yml up -d --build frontend
            fi
            
            echo "Frontend updated"
EOF
        
        print_success "Frontend updated"
    fi
}

# Update scraper
update_scraper() {
    if [ "$UPDATE_SCRAPER" = true ]; then
        print_status "Updating scraper..."
        
        # Copy scraper files
        sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no -r $LOCAL_PATH/SRM-Academia-Scraper-node-main/* $SERVER_USER@$SERVER_HOST:/home/srmadmin/SRM-Academia-Scraper-node-main/
        
        # Update scraper on server
        sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST << EOF
            cd $SERVER_PATH
            
            # Stop scraper container
            docker-compose -f docker-compose.prod.yml stop scraper || true
            
            # Rebuild and start scraper
            if [ "$NO_REBUILD" = true ]; then
                docker-compose -f docker-compose.prod.yml up -d scraper
            else
                docker-compose -f docker-compose.prod.yml up -d --build scraper
            fi
            
            echo "Scraper updated"
EOF
        
        print_success "Scraper updated"
    fi
}

# Health check
health_check() {
    print_status "Performing health check..."
    
    # Check backend
    if curl -s http://172.16.0.60:8000/health > /dev/null 2>&1; then
        print_success "Backend: Healthy"
    else
        print_error "Backend: Unhealthy"
        return 1
    fi
    
    # Check scraper
    if curl -s http://172.16.0.60:3001/health > /dev/null 2>&1; then
        print_success "Scraper: Healthy"
    else
        print_error "Scraper: Unhealthy"
        return 1
    fi
    
    # Check frontend
    if curl -s http://172.16.0.60/ > /dev/null 2>&1; then
        print_success "Frontend: Healthy"
    else
        print_error "Frontend: Unhealthy"
        return 1
    fi
}

# Main update process
main() {
    print_status "Starting BrokeBuy update process..."
    
    # Show what will be updated
    echo "Update plan:"
    [ "$UPDATE_BACKEND" = true ] && echo "  ✅ Backend"
    [ "$UPDATE_FRONTEND" = true ] && echo "  ✅ Frontend"
    [ "$UPDATE_SCRAPER" = true ] && echo "  ✅ Scraper"
    [ "$NO_REBUILD" = true ] && echo "  ⚡ No rebuild (faster)"
    
    echo ""
    read -p "Continue with update? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Update cancelled"
        exit 0
    fi
    
    # Perform updates
    update_backend
    update_frontend
    update_scraper
    
    # Wait for services to be ready
    print_status "Waiting for services to start..."
    sleep 10
    
    # Health check
    if health_check; then
        print_success "🎉 Update completed successfully!"
        print_status "Services available at:"
        print_status "  Frontend: http://172.16.0.60"
        print_status "  Backend API: http://172.16.0.60:8000"
        print_status "  API Docs: http://172.16.0.60:8000/docs"
        print_status "  Scraper: http://172.16.0.60:3001"
    else
        print_error "❌ Update completed but some services are unhealthy"
        print_status "Check logs with: ./server-management.sh logs"
        exit 1
    fi
}

# Run main function
main "$@"
