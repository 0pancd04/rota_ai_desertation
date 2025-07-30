#!/bin/bash

# Development logs script for AI Rota System
# This script shows logs from the development environment

echo "📋 Showing AI Rota System Development Logs..."
echo ""

# Show logs with follow option
echo "🔍 Press Ctrl+C to stop following logs"
echo ""

docker compose -f docker-compose.dev.yml logs -f 