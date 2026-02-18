#!/bin/bash

echo "🚀 FDA Regulatory Automation Platform - Quickstart"
echo "=================================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed"
    echo "Please install Docker from https://www.docker.com/get-started"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: Docker Compose is not installed"
    echo "Please install Docker Compose"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your ANTHROPIC_API_KEY"
    echo "   Open .env in a text editor and set:"
    echo "   ANTHROPIC_API_KEY=your-key-here"
    echo ""
    read -p "Press Enter after updating .env file..."
fi

# Verify API key is set
if ! grep -q "ANTHROPIC_API_KEY=sk-" .env; then
    echo ""
    echo "⚠️  WARNING: ANTHROPIC_API_KEY not set in .env"
    echo "   The platform will not work without a valid Claude API key"
    echo ""
    read -p "Do you want to continue anyway? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "🏗️  Building Docker containers..."
docker-compose build

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo ""
echo "🏥 Checking service health..."

# Check PostgreSQL
if docker-compose exec -T postgres pg_isready -U fda_user > /dev/null 2>&1; then
    echo "✅ PostgreSQL is healthy"
else
    echo "❌ PostgreSQL is not healthy"
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is healthy"
else
    echo "❌ Redis is not healthy"
fi

# Check Backend
if curl -s http://localhost:8400/health > /dev/null 2>&1; then
    echo "✅ Backend API is healthy"
else
    echo "⏳ Backend API is starting..."
    sleep 5
fi

# Check Frontend
if curl -s http://localhost:3400 > /dev/null 2>&1; then
    echo "✅ Frontend is healthy"
else
    echo "⏳ Frontend is starting..."
    sleep 5
fi

echo ""
echo "🌱 Seeding database with sample predicate devices..."
docker-compose exec -T backend python seed_data.py

echo ""
echo "✅ FDA Regulatory Automation Platform is ready!"
echo ""
echo "📍 Access points:"
echo "   Frontend:  http://localhost:3400"
echo "   Backend:   http://localhost:8400"
echo "   API Docs:  http://localhost:8400/api/docs"
echo ""
echo "🎯 Quick actions:"
echo "   1. Go to http://localhost:3400/submit to create a new submission"
echo "   2. View dashboard at http://localhost:3400"
echo "   3. Review submissions at http://localhost:3400/review"
echo ""
echo "📊 View logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 Stop services:"
echo "   docker-compose down"
echo ""
echo "Happy automating! 🎉"
