#!/bin/bash
# Frontend Startup Script
# Launches the React trading dashboard on http://localhost:3000

set -e

echo "=========================================="
echo "🚀 Starting Trading Dashboard Frontend"
echo "=========================================="

cd "$(dirname "$0")"

# Check if node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

echo "✓ Dependencies ready"
echo ""
echo "📊 Starting React development server..."
echo "   Dashboard available at: http://localhost:3000"
echo ""
echo "ℹ️  Make sure the backend API is running:"
echo "   • Run: python /Users/hari/Desktop/copilot_trade/backend/main.py"
echo "   • API available at: http://localhost:8000"
echo ""

cd frontend
npm start
