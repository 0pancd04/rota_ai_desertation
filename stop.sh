#!/bin/bash
echo "Stopping AI Rota System..."

# Find and kill the uvicorn process
pkill -f "uvicorn app.main:app"

echo "AI Rota System stopped." 