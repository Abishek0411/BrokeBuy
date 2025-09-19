#!/bin/bash

# Install sshpass for password authentication
# This script installs sshpass on the local machine

echo "🔧 Installing sshpass for password authentication..."

# Check if running on Ubuntu/Debian
if command -v apt-get &> /dev/null; then
    echo "Installing sshpass via apt-get..."
    sudo apt-get update
    sudo apt-get install -y sshpass
elif command -v yum &> /dev/null; then
    echo "Installing sshpass via yum..."
    sudo yum install -y sshpass
elif command -v dnf &> /dev/null; then
    echo "Installing sshpass via dnf..."
    sudo dnf install -y sshpass
elif command -v pacman &> /dev/null; then
    echo "Installing sshpass via pacman..."
    sudo pacman -S sshpass
elif command -v brew &> /dev/null; then
    echo "Installing sshpass via brew..."
    brew install sshpass
else
    echo "❌ Package manager not supported. Please install sshpass manually."
    echo "Download from: https://sourceforge.net/projects/sshpass/"
    exit 1
fi

# Verify installation
if command -v sshpass &> /dev/null; then
    echo "✅ sshpass installed successfully!"
    echo "Version: $(sshpass -V)"
else
    echo "❌ sshpass installation failed!"
    exit 1
fi

echo "🎉 Ready for password-based SSH authentication!"
