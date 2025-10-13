#!/bin/bash

# GitCloud Website - Local Development Server
# This script starts a local HTTP server to view the website

PORT=8000
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "  ██████╗ ██╗████████╗ ██████╗██╗      ██████╗ ██╗   ██╗██████╗ "
echo " ██╔════╝ ██║╚══██╔══╝██╔════╝██║     ██╔═══██╗██║   ██║██╔══██╗"
echo " ██║  ███╗██║   ██║   ██║     ██║     ██║   ██║██║   ██║██║  ██║"
echo " ██║   ██║██║   ██║   ██║     ██║     ██║   ██║██║   ██║██║  ██║"
echo " ╚██████╔╝██║   ██║   ╚██████╗███████╗╚██████╔╝╚██████╔╝██████╔╝"
echo "  ╚═════╝ ╚═╝   ╚═╝    ╚═════╝╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝ "
echo -e "${NC}"
echo ""
echo -e "${GREEN}Starting GitCloud Website...${NC}"
echo ""

# Check if port is already in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port $PORT is already in use. Stopping existing server..."
    kill $(lsof -t -i:$PORT) 2>/dev/null
    sleep 1
fi

# Start server based on available tools
if command -v python3 &> /dev/null; then
    echo "✓ Starting Python HTTP server on port $PORT..."
    echo ""
    echo -e "${GREEN}🚀 Website is running at:${NC}"
    echo -e "   ${BLUE}http://localhost:$PORT${NC}"
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo ""
    python3 -m http.server $PORT
elif command -v python &> /dev/null; then
    echo "✓ Starting Python HTTP server on port $PORT..."
    echo ""
    echo -e "${GREEN}🚀 Website is running at:${NC}"
    echo -e "   ${BLUE}http://localhost:$PORT${NC}"
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo ""
    python -m SimpleHTTPServer $PORT
elif command -v php &> /dev/null; then
    echo "✓ Starting PHP built-in server on port $PORT..."
    echo ""
    echo -e "${GREEN}🚀 Website is running at:${NC}"
    echo -e "   ${BLUE}http://localhost:$PORT${NC}"
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo ""
    php -S localhost:$PORT
else
    echo "❌ Error: No suitable HTTP server found."
    echo "Please install Python 3, Python 2, or PHP to run this script."
    echo ""
    echo "Or open index.html directly in your browser."
    exit 1
fi
