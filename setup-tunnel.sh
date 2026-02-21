#!/bin/bash

# Cloudflare Tunnel Setup Script
# This script helps you set up Cloudflare Tunnel for free global access

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
SERVER_PASSWORD="SRM_admin"
TUNNEL_NAME="brokebuy-srm"
SUBDOMAIN="brokebuy-srm"

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
    echo "Cloudflare Tunnel Setup Script"
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
}

# Parse command line arguments
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

# Setup tunnel on server
setup_tunnel() {
    print_status "Setting up Cloudflare Tunnel on server..."
    
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST << EOF
        cd /home/srmadmin/BrokeBuy
        
        # Check if cloudflared is installed
        if ! command -v cloudflared &> /dev/null; then
            echo "Installing Cloudflare Tunnel..."
            wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
            sudo dpkg -i cloudflared-linux-amd64.deb
            rm cloudflared-linux-amd64.deb
        fi
        
        echo "Cloudflare Tunnel is ready!"
        echo ""
        echo "Next steps:"
        echo "1. Run: cloudflared tunnel login"
        echo "2. Run: cloudflared tunnel create $TUNNEL_NAME"
        echo "3. Run: cloudflared tunnel run $TUNNEL_NAME"
        echo ""
        echo "This will create: https://$SUBDOMAIN.trycloudflare.com"
EOF
    
    print_success "Tunnel setup completed on server"
}

# Interactive tunnel setup
interactive_setup() {
    print_status "Starting interactive tunnel setup..."
    
    print_warning "You need to run these commands on the server:"
    echo ""
    echo "1. Connect to server:"
    echo "   ssh srmadmin@172.16.0.60"
    echo ""
    echo "2. Login to Cloudflare (opens browser):"
    echo "   cloudflared tunnel login"
    echo ""
    echo "3. Create tunnel:"
    echo "   cloudflared tunnel create $TUNNEL_NAME"
    echo ""
    echo "4. Run tunnel:"
    echo "   cloudflared tunnel run $TUNNEL_NAME"
    echo ""
    echo "5. Your app will be available at:"
    echo "   https://$SUBDOMAIN.trycloudflare.com"
    echo ""
    
    read -p "Press Enter when you're ready to connect to the server..."
    
    # Connect to server
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST
}

# Main function
main() {
    print_status "Cloudflare Tunnel Setup for BrokeBuy"
    print_status "Tunnel name: $TUNNEL_NAME"
    print_status "Subdomain: $SUBDOMAIN.trycloudflare.com"
    echo ""
    
    print_warning "This will set up Cloudflare Tunnel for free global access to your BrokeBuy application."
    print_warning "You'll need a free Cloudflare account."
    echo ""
    
    read -p "Continue with tunnel setup? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Tunnel setup cancelled"
        exit 0
    fi
    
    setup_tunnel
    interactive_setup
}

# Run main function
main "$@"
