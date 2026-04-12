#!/bin/bash

# ============================================================
# AI Trading Platform - Quick Start Script
# ============================================================

set -e  # Exit on error

echo "============================================================"
echo "AI Trading Platform - Quick Setup"
echo "============================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9+"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"
echo ""

# Navigate to backend directory
cd backend

# Create virtual environment
echo "Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠ .env file not found"
    echo ""
    echo "Creating .env template..."
    cat > .env << 'EOF'
# Claude AI Configuration
CLAUDE_API_KEY=your_claude_api_key_here
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Groww API Configuration
GROWW_API_KEY=your_groww_api_key
GROWW_API_SECRET=your_groww_api_secret
GROWW_AUTH_TOKEN=your_groww_auth_token
GROWW_API_BASE_URL=https://api.groww.in

# Trading Configuration
PAPER_TRADING_INITIAL_CAPITAL=100000
LIVE_TRADING_ENABLED=false
TRADING_SLIPPAGE_PERCENT=0.05
TRADING_COMMISSION_PERCENT=0.02

# Database
DATABASE_URL=sqlite:///./trading.db

# Logging
LOG_LEVEL=INFO

# App Configuration
APP_NAME=AI Trading Platform
APP_VERSION=1.0.0
DEBUG=false
EOF
    echo "✓ .env template created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env with your API credentials:"
    echo "   nano .env"
    echo ""
    echo "   Required credentials:"
    echo "   - CLAUDE_API_KEY: Get from https://console.anthropic.com"
    echo "   - GROWW_API_KEY, GROWW_API_SECRET, GROWW_AUTH_TOKEN"
    echo ""
else
    echo "✓ .env file found"
fi

echo ""
echo "============================================================"
echo "✅ Setup Complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Configure your API keys in .env"
echo "2. Run the platform:"
echo ""
echo "   python main.py"
echo ""
echo "3. Open in browser:"
echo ""
echo "   • API Documentation: http://localhost:8000/docs"
echo "   • ReDoc: http://localhost:8000/redoc"
echo "   • Health Check: http://localhost:8000/health"
echo ""
echo "For detailed setup instructions, see: ../SETUP_GUIDE.md"
echo ""
echo "============================================================"
echo ""
