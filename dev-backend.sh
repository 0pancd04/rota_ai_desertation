#!/bin/bash

# Backend-only development startup script for AI Rota System
# This script starts the backend with hot reloading and production frontend

set -e

echo "🚀 Starting AI Rota System Backend Development Mode..."
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
echo "🔨 Building and starting backend development container..."
docker compose -f docker-compose.dev-backend.yml up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
echo "🔍 Checking service status..."
if docker compose -f docker-compose.dev-backend.yml ps | grep -q "Up"; then
    echo ""
    echo "✅ Backend development services are running!"
    echo ""
    echo "🌐 Frontend: http://localhost:3000"
    echo "🔧 Backend API: http://localhost:8000"
    echo "📚 API Documentation: http://localhost:8000/docs"
    echo ""
    echo "🔄 Backend hot reloading is enabled:"
    echo "   - Backend changes will auto-reload"
    echo "   - Frontend is production build (no hot reload)"
    echo ""
    echo "📝 Useful commands:"
    echo "   View logs: docker compose -f docker-compose.dev-backend.yml logs -f"
    echo "   Stop services: docker compose -f docker-compose.dev-backend.yml down"
    echo "   Restart backend: docker compose -f docker-compose.dev-backend.yml restart backend-dev"
    echo ""
    echo "🎯 Backend development mode is ready! Make changes to your backend code and see them immediately."
    echo "💡 For frontend development, run the frontend locally with: cd frontend && npm run dev"
else
    echo "❌ Error: Services failed to start"
    echo "Check logs with: docker compose -f docker-compose.dev-backend.yml logs"
    exit 1
fi 