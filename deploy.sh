#!/bin/bash

# BrokeBuy Production Deployment Script
# This script deploys the BrokeBuy application to the production server

set -e  # Exit on any error

echo "🚀 Starting BrokeBuy Production Deployment..."

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

# Function to print colored output
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

# Check if required files exist
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if [ ! -f "docker-compose.prod.yml" ]; then
        print_error "docker-compose.prod.yml not found!"
        exit 1
    fi
    
    if [ ! -f "env.prod.template" ]; then
        print_error "env.prod.template not found!"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Create environment file if it doesn't exist
setup_environment() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f ".env.prod" ]; then
        print_warning ".env.prod not found. Creating from template..."
        cp env.prod.template .env.prod
        print_warning "Please edit .env.prod with your actual configuration values before deploying!"
        print_warning "Required values: MONGO_ROOT_PASSWORD, JWT_SECRET_KEY, CLOUDINARY_*"
        read -p "Press Enter to continue after editing .env.prod..."
    fi
    
    print_success "Environment configuration ready"
}

# Deploy to server
deploy_to_server() {
    print_status "Deploying to server $SERVER_USER@$SERVER_HOST..."
    
    # Check if sshpass is installed
    if ! command -v sshpass &> /dev/null; then
        print_status "Installing sshpass for password authentication..."
        sudo apt-get update && sudo apt-get install -y sshpass
    fi
    
    # Create directory on server
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST "mkdir -p $SERVER_PATH"
    
    # Copy project files to server
    print_status "Copying project files..."
    sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no -r $LOCAL_PATH/proj_BrokeBuy_backend/* $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
    sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no -r $LOCAL_PATH/proj_BrokeBuy_frontend $SERVER_USER@$SERVER_HOST:$SERVER_PATH/../
    sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no -r $LOCAL_PATH/SRM-Academia-Scraper-node-main $SERVER_USER@$SERVER_HOST:$SERVER_PATH/../
    
    print_success "Files copied to server"
}

# Setup and start services on server
setup_server() {
    print_status "Setting up services on server..."
    
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST << 'EOF'
        cd /home/srmadmin/brokebuy
        
        # Install Docker if not present
        if ! command -v docker &> /dev/null; then
            echo "Installing Docker..."
            curl -fsSL https://get.docker.com -o get-docker.sh
            sh get-docker.sh
            sudo usermod -aG docker $USER
            rm get-docker.sh
        fi
        
        # Install Docker Compose if not present
        if ! command -v docker-compose &> /dev/null; then
            echo "Installing Docker Compose..."
            sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
            sudo chmod +x /usr/local/bin/docker-compose
        fi
        
        # Stop any existing containers
        docker-compose -f docker-compose.prod.yml down || true
        
        # Build and start services
        echo "Building and starting services..."
        docker-compose -f docker-compose.prod.yml up -d --build
        
        # Wait for services to be ready
        echo "Waiting for services to start..."
        sleep 30
        
        # Check service status
        echo "Checking service status..."
        docker-compose -f docker-compose.prod.yml ps
        
        echo "Deployment completed!"
        echo "Services available at:"
        echo "  Frontend: http://172.16.0.60"
        echo "  Backend API: http://172.16.0.60:8000"
        echo "  API Docs: http://172.16.0.60:8000/docs"
        echo "  Scraper: http://172.16.0.60:3001"
EOF
    
    print_success "Server setup completed"
}

# Main deployment process
main() {
    print_status "Starting BrokeBuy deployment process..."
    
    check_prerequisites
    setup_environment
    deploy_to_server
    setup_server
    
    print_success "🎉 Deployment completed successfully!"
    print_status "Your BrokeBuy application is now running on:"
    print_status "  Frontend: http://172.16.0.60"
    print_status "  Backend API: http://172.16.0.60:8000"
    print_status "  API Documentation: http://172.16.0.60:8000/docs"
    print_status "  Scraper Service: http://172.16.0.60:3001"
    
    print_status "To manage your deployment:"
    print_status "  View logs: ssh $SERVER_USER@$SERVER_HOST 'cd $SERVER_PATH && docker-compose -f docker-compose.prod.yml logs'"
    print_status "  Stop services: ssh $SERVER_USER@$SERVER_HOST 'cd $SERVER_PATH && docker-compose -f docker-compose.prod.yml down'"
    print_status "  Restart services: ssh $SERVER_USER@$SERVER_HOST 'cd $SERVER_PATH && docker-compose -f docker-compose.prod.yml restart'"
}

# Run main function
main "$@"
