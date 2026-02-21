#!/bin/bash

# BrokeBuy Domain Deployment Script
# This script deploys BrokeBuy with domain configuration

set -e  # Exit on any error

echo "🌐 Starting BrokeBuy Domain Deployment..."

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
    echo "BrokeBuy Domain Deployment Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --domain DOMAIN    Set domain name (e.g., yourdomain.com)"
    echo "  --ssl-email EMAIL  Set email for SSL certificate"
    echo "  --no-ssl          Skip SSL certificate setup"
    echo "  --help            Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 --domain srmbrokebuy.com --ssl-email admin@srmbrokebuy.com"
    echo ""
}

# Parse command line arguments
DOMAIN_NAME=""
SSL_EMAIL=""
NO_SSL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --domain)
            DOMAIN_NAME="$2"
            shift 2
            ;;
        --ssl-email)
            SSL_EMAIL="$2"
            shift 2
            ;;
        --no-ssl)
            NO_SSL=true
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

# Validate required parameters
if [ -z "$DOMAIN_NAME" ]; then
    print_error "Domain name is required!"
    echo "Usage: $0 --domain yourdomain.com"
    exit 1
fi

if [ "$NO_SSL" = false ] && [ -z "$SSL_EMAIL" ]; then
    print_error "SSL email is required for SSL certificate setup!"
    echo "Usage: $0 --domain yourdomain.com --ssl-email your-email@example.com"
    exit 1
fi

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

# Create environment file with domain configuration
setup_environment() {
    print_status "Setting up environment configuration with domain..."
    
    if [ ! -f ".env.prod" ]; then
        print_warning ".env.prod not found. Creating from template..."
        cp env.prod.template .env.prod
    fi
    
    # Add domain configuration
    echo "" >> .env.prod
    echo "# Domain Configuration" >> .env.prod
    echo "DOMAIN_NAME=$DOMAIN_NAME" >> .env.prod
    echo "SSL_EMAIL=$SSL_EMAIL" >> .env.prod
    echo "ENVIRONMENT=production" >> .env.prod
    
    print_success "Environment configuration ready with domain: $DOMAIN_NAME"
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
    print_status "Deploying to server $SERVER_USER@$SERVER_HOST with domain: $DOMAIN_NAME..."
    
    # Check if sshpass is installed
    if ! command -v sshpass &> /dev/null; then
        print_status "Installing sshpass for password authentication..."
        sudo apt-get update && sudo apt-get install -y sshpass
    fi
    
    # Create directories on server
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST "mkdir -p $SERVER_BASE_PATH/backend $SERVER_BASE_PATH/frontend $SERVER_BASE_PATH/scraper $SERVER_BASE_PATH/nginx/ssl $SERVER_BASE_PATH/nginx/conf.d"
    
    # Copy source files to server (much faster now)
    print_status "Copying source files to server..."
    sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no -r "$temp_dir/backend"/* $SERVER_USER@$SERVER_HOST:$SERVER_BASE_PATH/backend/
    sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no -r "$temp_dir/frontend"/* $SERVER_USER@$SERVER_HOST:$SERVER_BASE_PATH/frontend/
    sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no -r "$temp_dir/scraper"/* $SERVER_USER@$SERVER_HOST:$SERVER_BASE_PATH/scraper/
    
    print_success "Source files copied to server"
}

# Create nginx configuration for domain
create_nginx_config() {
    print_status "Creating nginx configuration for domain: $DOMAIN_NAME..."
    
    # Create nginx configuration
    cat > /tmp/nginx.conf << EOF
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }
    
    upstream frontend {
        server frontend:80;
    }
    
    upstream scraper {
        server scraper:3001;
    }

    # HTTP to HTTPS redirect
    server {
        listen 80;
        server_name $DOMAIN_NAME www.$DOMAIN_NAME;
        return 301 https://\$server_name\$request_uri;
    }

    # Main HTTPS server
    server {
        listen 443 ssl http2;
        server_name $DOMAIN_NAME www.$DOMAIN_NAME;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        # Backend API
        location /api/ {
            proxy_pass http://backend/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        # Scraper API
        location /scraper/ {
            proxy_pass http://scraper/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
    }
}
EOF

    # Copy nginx configuration to server
    sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no /tmp/nginx.conf $SERVER_USER@$SERVER_HOST:$SERVER_BASE_PATH/nginx/
    
    print_success "Nginx configuration created for domain: $DOMAIN_NAME"
}

# Setup SSL certificate
setup_ssl() {
    if [ "$NO_SSL" = true ]; then
        print_warning "Skipping SSL certificate setup"
        return
    fi
    
    print_status "Setting up SSL certificate for domain: $DOMAIN_NAME..."
    
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST << EOF
        cd $SERVER_BASE_PATH
        
        # Install certbot if not present
        if ! command -v certbot &> /dev/null; then
            echo "Installing certbot..."
            sudo apt-get update
            sudo apt-get install -y certbot
        fi
        
        # Stop nginx temporarily for certificate generation
        docker-compose -f backend/docker-compose.prod.yml stop nginx || true
        
        # Get SSL certificate
        echo "Getting SSL certificate for $DOMAIN_NAME..."
        sudo certbot certonly --standalone -d $DOMAIN_NAME -d www.$DOMAIN_NAME --email $SSL_EMAIL --agree-tos --non-interactive
        
        # Copy certificates to nginx directory
        sudo cp /etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem ./nginx/ssl/cert.pem
        sudo cp /etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem ./nginx/ssl/key.pem
        sudo chown \$USER:\$USER ./nginx/ssl/cert.pem ./nginx/ssl/key.pem
        
        echo "SSL certificate setup completed"
EOF
    
    print_success "SSL certificate setup completed for domain: $DOMAIN_NAME"
}

# Setup and start services on server
setup_server() {
    print_status "Setting up services on server with domain configuration..."
    
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
        echo "Building and starting services with domain configuration..."
        docker-compose -f docker-compose.prod.yml up -d --build
        
        # Wait for services to be ready
        echo "Waiting for services to start..."
        sleep 30
        
        # Check service status
        echo "Checking service status..."
        docker-compose -f docker-compose.prod.yml ps
        
        echo "Domain deployment completed!"
        echo "Services available at:"
        echo "  Frontend: https://$DOMAIN_NAME"
        echo "  Backend API: https://$DOMAIN_NAME/api"
        echo "  API Docs: https://$DOMAIN_NAME/api/docs"
        echo "  Scraper: https://$DOMAIN_NAME/scraper"
EOF
    
    print_success "Server setup completed with domain configuration"
}

# Cleanup temporary files
cleanup() {
    local temp_dir=$1
    if [ -n "$temp_dir" ] && [ -d "$temp_dir" ]; then
        print_status "Cleaning up temporary files..."
        rm -rf "$temp_dir"
        rm -f /tmp/nginx.conf
        print_success "Cleanup completed"
    fi
}

# Main deployment process
main() {
    print_status "Starting BrokeBuy domain deployment process..."
    print_status "Domain: $DOMAIN_NAME"
    print_status "SSL Email: $SSL_EMAIL"
    print_status "SSL Setup: $([ "$NO_SSL" = true ] && echo "Disabled" || echo "Enabled")"
    
    # Trap to ensure cleanup on exit
    trap 'cleanup "$TEMP_DIR"' EXIT
    
    check_prerequisites
    setup_environment
    
    # Prepare source files
    TEMP_DIR=$(prepare_source_files)
    
    # Deploy to server
    deploy_to_server "$TEMP_DIR"
    
    # Create nginx configuration
    create_nginx_config
    
    # Setup SSL certificate
    setup_ssl
    
    # Setup server
    setup_server
    
    print_success "🎉 Domain deployment completed successfully!"
    print_status "Your BrokeBuy application is now accessible at:"
    print_status "  🌐 Main Site: https://$DOMAIN_NAME"
    print_status "  🔧 Backend API: https://$DOMAIN_NAME/api"
    print_status "  📚 API Documentation: https://$DOMAIN_NAME/api/docs"
    print_status "  🔍 Scraper Service: https://$DOMAIN_NAME/scraper"
    
    print_status "To manage your deployment:"
    print_status "  View logs: ./server-management.sh logs"
    print_status "  Stop services: ./server-management.sh stop"
    print_status "  Restart services: ./server-management.sh restart"
    
    print_warning "Important: Make sure to configure DNS settings in GoDaddy to point $DOMAIN_NAME to $SERVER_HOST"
}

# Run main function
main "$@"
