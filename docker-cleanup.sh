#!/bin/bash

# Docker cleanup script to free up resources
# This script cleans up Docker resources when not in use

echo "🧹 Docker Cleanup Script"
echo "========================"

# Function to confirm action
confirm() {
    read -p "$1 (y/N): " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

echo "Current Docker resource usage:"
sudo docker system df

echo ""
echo "Available cleanup options:"
echo "1. Remove stopped containers"
echo "2. Remove unused images"
echo "3. Remove unused volumes"
echo "4. Remove unused networks"
echo "5. Complete cleanup (all of the above)"
echo "6. Prune everything (aggressive cleanup)"

read -p "Choose an option (1-6): " choice

case $choice in
    1)
        if confirm "Remove all stopped containers?"; then
            sudo docker container prune -f
            echo "✅ Stopped containers removed"
        fi
        ;;
    2)
        if confirm "Remove unused images?"; then
            sudo docker image prune -f
            echo "✅ Unused images removed"
        fi
        ;;
    3)
        if confirm "Remove unused volumes?"; then
            sudo docker volume prune -f
            echo "✅ Unused volumes removed"
        fi
        ;;
    4)
        if confirm "Remove unused networks?"; then
            sudo docker network prune -f
            echo "✅ Unused networks removed"
        fi
        ;;
    5)
        if confirm "Perform complete cleanup?"; then
            sudo docker system prune -f
            echo "✅ Complete cleanup performed"
        fi
        ;;
    6)
        if confirm "⚠️  WARNING: This will remove ALL unused Docker resources. Continue?"; then
            sudo docker system prune -a --volumes -f
            echo "✅ Aggressive cleanup performed"
        fi
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

echo ""
echo "Updated Docker resource usage:"
sudo docker system df
