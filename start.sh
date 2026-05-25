#!/bin/bash
# Quick start script for RAG system

echo "========================================="
echo "RAG E-commerce Support System - Setup"
echo "========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker is installed"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and set your BOT_TOKEN before continuing"
    echo ""
    read -p "Press Enter when ready to continue..."
fi

echo "🚀 Starting RAG system..."
echo ""

# Start services
docker-compose up --build -d

echo ""
echo "========================================="
echo "Waiting for services to start..."
echo "========================================="
echo ""

# Wait for services
sleep 30

# Check health
echo "🔍 Checking service health..."
echo ""

if curl -f http://localhost:8000/health &> /dev/null; then
    echo "✅ Backend is running: http://localhost:8000"
    echo "📚 API Documentation: http://localhost:8000/docs"
    echo "📊 Prometheus Metrics: http://localhost:8000/metrics"
else
    echo "❌ Backend is not responding. Check logs: docker-compose logs backend"
fi

echo ""
echo "🖥️  Admin Panel (Appsmith): http://localhost:8080"
echo "   Setup guide: docs/APPSMITH_SETUP.md"

echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "========================================="
echo "🎉 Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Check API docs: http://localhost:8000/docs"
echo "2. Upload documents via /api/documents/upload"
echo "3. Test your bot in Telegram"
echo ""
echo "View logs: docker-compose logs -f"
echo "Stop services: docker-compose down"
echo ""
