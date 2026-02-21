#!/bin/bash

# BrokeBuy Free Deployment Script
# This script deploys BrokeBuy using Cloudflare Tunnel (100% Free)

set -e  # Exit on any error

echo "🆓 Starting BrokeBuy Free Deployment with Cloudflare Tunnel..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVER_USER="srmadmin"
SERVER_HOST="172.16.0.60"
SERVER_PASSWORD="SRM_admin"
SERVER_BASE_PATH="/home/srmadmin/BrokeBuy"
SERVER_PATH="/home/srmadmin/BrokeBuy/backend"
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

# Function to show usage
show_usage() {
    echo "BrokeBuy Free Deployment Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --tunnel-name NAME    Set tunnel name (default: brokebuy-srm)"
    echo "  --subdomain NAME      Set subdomain (default: brokebuy-srm)"
    echo "  --help               Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 --tunnel-name brokebuy-srm --subdomain brokebuy-srm"
    echo ""
    echo "This will create: https://brokebuy-srm.trycloudflare.com"
    echo ""
}

# Parse command line arguments
TUNNEL_NAME="brokebuy-srm"
SUBDOMAIN="brokebuy-srm"

while [[ $# -gt 0 ]]; do
    case $1 in
        --tunnel-name)
            TUNNEL_NAME="$2"
            shift 2
            ;;
        --subdomain)
            SUBDOMAIN="$2"
            shift 2
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

# Create environment file
setup_environment() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f ".env.prod" ]; then
        print_warning ".env.prod not found. Creating from template..."
        cp env.prod.template .env.prod
        print_warning "Please edit .env.prod with your actual configuration values!"
        read -p "Press Enter to continue after editing .env.prod..."
    fi
    
    # Add tunnel configuration
    echo "" >> .env.prod
    echo "# Cloudflare Tunnel Configuration" >> .env.prod
    echo "TUNNEL_NAME=$TUNNEL_NAME" >> .env.prod
    echo "SUBDOMAIN=$SUBDOMAIN" >> .env.prod
    echo "ENVIRONMENT=production" >> .env.prod
    
    print_success "Environment configuration ready"
}

# Create optimized copy of project files
prepare_source_files() {
    print_status "Preparing source files (excluding node_modules, myenv, etc.)..."
    
    # Create temporary directory for clean source files
    TEMP_DIR="/tmp/brokebuy-deploy-$(date +%s)"
    mkdir -p "$TEMP_DIR"
    
    # Copy backend (exclude myenv, __pycache__, .git)
    print_status "Preparing backend source..."
    rsync -av --exclude='myenv/' \
              --exclude='__pycache__/' \
              --exclude='.git/' \
              --exclude='*.pyc' \
              --exclude='.pytest_cache/' \
              --exclude='*.log' \
              --exclude='.pid' \
              "$LOCAL_PATH/proj_BrokeBuy_backend/" "$TEMP_DIR/backend/"
    
    # Copy frontend (exclude node_modules, .git, dist)
    print_status "Preparing frontend source..."
    rsync -av --exclude='node_modules/' \
              --exclude='.git/' \
              --exclude='dist/' \
              --exclude='.vite/' \
              --exclude='*.log' \
              "$LOCAL_PATH/proj_BrokeBuy_frontend/srm-brokebuy-vibe/" "$TEMP_DIR/frontend/"
    
    # Copy scraper (exclude node_modules, .git)
    print_status "Preparing scraper source..."
    rsync -av --exclude='node_modules/' \
              --exclude='.git/' \
              --exclude='*.log' \
              "$LOCAL_PATH/SRM-Academia-Scraper-node-main/server/" "$TEMP_DIR/scraper/"
    
    print_success "Source files prepared in $TEMP_DIR"
    echo "$TEMP_DIR"
}

# Deploy to server
deploy_to_server() {
    local temp_dir=$1
    print_status "Deploying to server $SERVER_USER@$SERVER_HOST..."
    
    # Check if sshpass is installed
    if ! command -v sshpass &> /dev/null; then
        print_status "Installing sshpass for password authentication..."
        sudo apt-get update && sudo apt-get install -y sshpass
    fi
    
    # Create directories on server
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST "mkdir -p $SERVER_BASE_PATH/backend $SERVER_BASE_PATH/frontend $SERVER_BASE_PATH/scraper"
    
    # Copy source files to server (much faster now)
    print_status "Copying source files to server..."
    sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no -r "$temp_dir/backend"/* $SERVER_USER@$SERVER_HOST:$SERVER_BASE_PATH/backend/
    sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no -r "$temp_dir/frontend"/* $SERVER_USER@$SERVER_HOST:$SERVER_BASE_PATH/frontend/
    sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no -r "$temp_dir/scraper"/* $SERVER_USER@$SERVER_HOST:$SERVER_BASE_PATH/scraper/
    
    print_success "Source files copied to server"
}

# Install and setup Cloudflare Tunnel
setup_cloudflare_tunnel() {
    print_status "Setting up Cloudflare Tunnel for free global access..."
    
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST << EOF
        cd $SERVER_BASE_PATH
        
        # Install Cloudflare Tunnel if not present
        if ! command -v cloudflared &> /dev/null; then
            echo "Installing Cloudflare Tunnel..."
            wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
            sudo dpkg -i cloudflared-linux-amd64.deb
            rm cloudflared-linux-amd64.deb
        fi
        
        # Create tunnel configuration
        cat > tunnel-config.yml << 'TUNNEL_EOF'
tunnel: $TUNNEL_NAME
credentials-file: /home/srmadmin/.cloudflared/$TUNNEL_NAME.json

ingress:
  - hostname: $SUBDOMAIN.trycloudflare.com
    service: http://localhost:80
  - service: http_status:404
TUNNEL_EOF
        
        echo "Cloudflare Tunnel configuration created"
        echo "Tunnel name: $TUNNEL_NAME"
        echo "Subdomain: $SUBDOMAIN.trycloudflare.com"
EOF
    
    print_success "Cloudflare Tunnel setup completed"
    print_warning "IMPORTANT: You need to run the following commands on the server:"
    print_warning "1. cloudflared tunnel login"
    print_warning "2. cloudflared tunnel create $TUNNEL_NAME"
    print_warning "3. cloudflared tunnel run $TUNNEL_NAME"
}

# Setup and start services on server
setup_server() {
    print_status "Setting up services on server..."
    
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST << 'EOF'
        cd /home/srmadmin/BrokeBuy/backend
        
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
        
        # Build and start services (Docker will handle all installations)
        echo "Building and starting services..."
        docker-compose -f docker-compose.prod.yml up -d --build
        
        # Wait for services to be ready
        echo "Waiting for services to start..."
        sleep 30
        
        # Check service status
        echo "Checking service status..."
        docker-compose -f docker-compose.prod.yml ps
        
        echo "Services deployment completed!"
        echo "Local access:"
        echo "  Frontend: http://172.16.0.60"
        echo "  Backend API: http://172.16.0.60:8000"
        echo "  API Docs: http://172.16.0.60:8000/docs"
        echo "  Scraper: http://172.16.0.60:3001"
EOF
    
    print_success "Server setup completed"
}

# Cleanup temporary files
cleanup() {
    local temp_dir=$1
    if [ -n "$temp_dir" ] && [ -d "$temp_dir" ]; then
        print_status "Cleaning up temporary files..."
        rm -rf "$temp_dir"
        print_success "Cleanup completed"
    fi
}

# Main deployment process
main() {
    print_status "Starting BrokeBuy free deployment process..."
    print_status "Tunnel name: $TUNNEL_NAME"
    print_status "Subdomain: $SUBDOMAIN.trycloudflare.com"
    
    # Trap to ensure cleanup on exit
    trap 'cleanup "$TEMP_DIR"' EXIT
    
    check_prerequisites
    setup_environment
    
    # Prepare source files
    TEMP_DIR=$(prepare_source_files)
    
    # Deploy to server
    deploy_to_server "$TEMP_DIR"
    
    # Setup Cloudflare Tunnel
    setup_cloudflare_tunnel
    
    # Setup server
    setup_server
    
    print_success "🎉 Free deployment completed successfully!"
    print_status "Your BrokeBuy application is now accessible at:"
    print_status "  🌐 Local Access: http://172.16.0.60"
    print_status "  🔧 Backend API: http://172.16.0.60:8000"
    print_status "  📚 API Documentation: http://172.16.0.60:8000/docs"
    print_status "  🔍 Scraper Service: http://172.16.0.60:3001"
    
    print_warning "To enable global access, run these commands on the server:"
    print_warning "  ssh srmadmin@172.16.0.60"
    print_warning "  cloudflared tunnel login"
    print_warning "  cloudflared tunnel create $TUNNEL_NAME"
    print_warning "  cloudflared tunnel run $TUNNEL_NAME"
    
    print_status "After tunnel setup, your app will be accessible at:"
    print_status "  🌍 Global Access: https://$SUBDOMAIN.trycloudflare.com"
    print_status "  🔧 Global API: https://$SUBDOMAIN.trycloudflare.com/api"
    print_status "  📚 Global Docs: https://$SUBDOMAIN.trycloudflare.com/api/docs"
    
    print_status "To manage your deployment:"
    print_status "  View logs: ./server-management.sh logs"
    print_status "  Stop services: ./server-management.sh stop"
    print_status "  Restart services: ./server-management.sh restart"
}

# Run main function
main "$@"
