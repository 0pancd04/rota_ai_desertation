#!/bin/bash

# AI Rota System for Healthcare - Docker Runner
echo "🚀 Starting AI Rota System for Healthcare..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create a .env file based on env.template with your API keys:"
    echo "cp env.template .env"
    echo "Then edit .env and add your API keys:"
    echo "- OPENAI_API_KEY=your_openai_api_key_here"
    echo "- GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here (optional)"
    exit 1
fi

# Build and start the services
echo "📦 Building and starting services..."
docker compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
if docker compose ps | grep -q "Up"; then
    echo "✅ Services are running!"
    echo ""
    echo "🌐 Frontend: http://localhost:3000"
    echo "🔧 Backend API: http://localhost:8000"
    echo "📚 API Documentation: http://localhost:8000/docs"
    echo ""
    echo "To stop the services, run: docker compose down"
    echo "To view logs, run: docker compose logs -f"
else
    echo "❌ Error: Services failed to start"
    echo "Check logs with: docker compose logs"
    exit 1
fi 