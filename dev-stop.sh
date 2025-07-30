#!/bin/bash

# Development stop script for AI Rota System
# This script stops the development environment

echo "🛑 Stopping AI Rota System Development Environment..."
echo ""

# Stop development containers
echo "📦 Stopping development containers..."
docker compose -f docker-compose.dev.yml down

echo ""
echo "✅ Development environment stopped successfully!"
echo ""
echo "💡 To start again, run: ./dev-start.sh" 