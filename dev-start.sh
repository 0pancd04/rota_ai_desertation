#!/bin/bash

# Development startup script for AI Rota System
# This script starts the development environment with hot reloading

set -e

echo "🚀 Starting AI Rota System in Development Mode..."
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found. Please create one from env.template"
    echo "   Copy env.template to .env and add your API keys"
    echo ""
fi

# Stop any existing containers
echo "🛑 Stopping any existing containers..."
docker compose down 2>/dev/null || true

# Build and start development containers
echo "🔨 Building and starting development containers..."
docker compose -f docker-compose.dev.yml up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
echo "🔍 Checking service status..."
if docker compose -f docker-compose.dev.yml ps | grep -q "Up"; then
    echo ""
    echo "✅ Development services are running!"
    echo ""
    echo "🌐 Frontend: http://localhost:3000"
    echo "🔧 Backend API: http://localhost:8000"
    echo "📚 API Documentation: http://localhost:8000/docs"
    echo ""
    echo "🔄 Hot reloading is enabled:"
    echo "   - Backend changes will auto-reload"
    echo "   - Frontend changes will auto-reload"
    echo ""
    echo "📝 Useful commands:"
    echo "   View logs: docker compose -f docker-compose.dev.yml logs -f"
    echo "   Stop services: docker compose -f docker-compose.dev.yml down"
    echo "   Restart services: docker compose -f docker-compose.dev.yml restart"
    echo ""
    echo "🎯 Development mode is ready! Make changes to your code and see them immediately."
else
    echo "❌ Error: Services failed to start"
    echo "Check logs with: docker compose -f docker-compose.dev.yml logs"
    exit 1
fi 