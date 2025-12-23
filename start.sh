#!/bin/bash

# Configuration Check
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please run: python3 setup.py"
    exit 1
fi

# Start Backend
echo "🚀 Starting Backend Services..."
export PYTHONPATH=$PYTHONPATH:$(pwd)
./venv/bin/python -m uvicorn api.main:app --reload --port 8000 &
BACKEND_PID=$!

# Start Frontend
echo "🌐 Starting Frontend Web UI..."
if [ -d "web" ]; then
    cd web
    npm run dev &
    FRONTEND_PID=$!
    cd ..
else
    echo "⚠️ Warning: 'web' directory not found. Frontend not started."
fi

# Handle shutdown
trap "kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT SIGTERM

echo "✅ Full stack is booting up. Check logs for details."
wait
