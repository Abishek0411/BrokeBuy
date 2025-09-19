#!/bin/bash

# Environment Setup Script for BrokeBuy
echo "🔐 BrokeBuy Environment Setup"
echo "=============================="

# Check if .env already exists
if [ -f .env ]; then
    echo "⚠️  .env file already exists!"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Setup cancelled."
        exit 1
    fi
fi

# Copy example file
echo "📋 Copying .env.example to .env..."
cp .env.example .env

# Check if .env.docker exists
if [ -f .env.docker ]; then
    echo "⚠️  .env.docker file already exists!"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "ℹ️  Skipping .env.docker creation."
    else
        echo "📋 Copying .env.example to .env.docker..."
        cp .env.example .env.docker
        # Update MONGO_URI for Docker
        sed -i 's|mongodb://localhost:27017/brokebuy|mongodb://mongodb:27017/brokebuy|g' .env.docker
    fi
else
    echo "📋 Copying .env.example to .env.docker..."
    cp .env.example .env.docker
    # Update MONGO_URI for Docker
    sed -i 's|mongodb://localhost:27017/brokebuy|mongodb://mongodb:27017/brokebuy|g' .env.docker
fi

echo ""
echo "✅ Environment files created successfully!"
echo ""
echo "🔧 Next steps:"
echo "1. Edit .env with your actual credentials:"
echo "   nano .env"
echo ""
echo "2. Edit .env.docker with your actual credentials:"
echo "   nano .env.docker"
echo ""
echo "3. Start the development environment:"
echo "   ./optimized-dev-start.sh"
echo ""
echo "📖 For detailed instructions, see ENVIRONMENT-SETUP.md"
